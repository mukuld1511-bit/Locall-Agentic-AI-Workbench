from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Generator, Optional

from .base import BaseModelAdapter, WorkerInferenceResponse


def _find_llama_server() -> str:
    candidates = []

    env_path = os.environ.get("LLAMA_SERVER")
    if env_path:
        candidates.append(Path(env_path))

    project_root = Path(__file__).resolve().parents[2]

    candidates.extend(
        [
            project_root / "runtime" / "llama" / "llama-server.exe",
            project_root / "runtime" / "llama" / "llama-server",
        ]
    )

    path_server = shutil.which("llama-server")
    if path_server:
        candidates.append(Path(path_server))

    # Linux compatibility.
    candidates.append(
        Path("/home/piet/llama.cpp/build/bin/llama-server")
    )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())

    raise FileNotFoundError(
        "llama-server executable not found. "
        "Set LLAMA_SERVER or place llama-server in runtime/llama."
    )


LLAMA_SERVER = _find_llama_server()


class LlamaCppAdapter(BaseModelAdapter):
    """
    Local llama.cpp / llama-server adapter.

    Each worker owns a dedicated endpoint:
        general  -> 8091
        coding   -> 8092
        vision   -> 8093
        document -> 8094

    The adapter NEVER considers /health alone sufficient to reuse
    an existing server. It also verifies /v1/models.
    """

    def __init__(
        self,
        worker_type: str,
        model_name: str,
        endpoint: str,
        vram_mb: int,
        mmproj_path: Optional[str] = None,
        media_path: Optional[str] = None,
    ):
        self.worker_type = worker_type
        self.model_name = model_name
        self.endpoint = endpoint.rstrip("/")
        self.vram_mb = int(vram_mb)

        project_root = Path(__file__).resolve().parents[2]

        self.mmproj_path = self._resolve_project_path(
            mmproj_path,
            project_root,
        )

        self.media_path = self._resolve_project_path(
            media_path,
            project_root,
        )

        self.process = None

        # True when the endpoint was already running before this
        # adapter took ownership of the logical worker.
        self._external_server = False

    # ============================================================
    # PATHS
    # ============================================================

    @staticmethod
    def _resolve_project_path(
        value: Optional[str],
        project_root: Path,
    ) -> Optional[str]:

        if not value:
            return None

        path = Path(value).expanduser()

        if not path.is_absolute():
            path = project_root / path

        return str(path.resolve())

    # ============================================================
    # MODEL IDENTITY
    # ============================================================

    def _configured_model_path(self) -> Optional[Path]:
        """
        Return the configured GGUF path for this worker.

        This is intentionally derived from the worker identity so that
        logical names such as:

            StarCoder2-3B-Instruct-Q4_K_M

        can be compared against actual llama-server identifiers such as:

            models/starcoder2-3b/
            starcoder2-3b-instruct.Q4_K_M.gguf
        """

        project_root = Path(__file__).resolve().parents[2]

        paths = {
            "general": (
                project_root
                / "models"
                / "qwen2.5-3b"
                / "qwen2.5-3b-instruct-q4_k_m.gguf"
            ),
            "coding": (
                project_root
                / "models"
                / "qwen2.5-coder-3b"
                / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
            ),
            "vision": (
                project_root
                / "models"
                / "Qwen2.5-VL-3B-Instruct-GGUF"
                / "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
            ),
            "document": (
                project_root
                / "models"
                / "gemma3-4b"
                / "google_gemma-3-4b-it-Q4_K_M.gguf"
            ),
        }

        return paths.get(self.worker_type)

    def _model_aliases(self) -> set[str]:
        aliases = set()

        configured = self._configured_model_path()

        if configured:
            aliases.add(configured.name.lower())
            aliases.add(configured.stem.lower())

        logical = str(self.model_name).strip().lower()

        aliases.add(logical)

        # Normalize common logical/filename differences.
        normalized = (
            logical
            .replace("_", "-")
            .replace(".gguf", "")
        )

        aliases.add(normalized)

        worker_aliases = {
            "general": {
                "qwen2.5-3b",
                "qwen2.5-3b-instruct",
                "qwen2.5-3b-instruct-q4_k_m",
            },
            "coding": {
                "qwen2.5-coder-3b",
                "qwen2.5-coder-3b-instruct",
                "qwen2.5-coder-3b-instruct-q4_k_m",
            },
            "vision": {
                "qwen2.5-vl-3b",
                "qwen2.5-vl-3b-instruct",
                "qwen2.5-vl-3b-instruct-q4_k_m",
            },
            "document": {
                "gemma-3-4b",
                "gemma3-4b",
                "google_gemma-3-4b-it-q4_k_m",
                "google_gemma-3-4b-it",
            },
        }

        aliases.update(worker_aliases.get(self.worker_type, set()))

        return {
            item.strip().lower()
            for item in aliases
            if item
        }

    def _model_matches(
        self,
        loaded_model: Optional[str],
    ) -> bool:

        if not loaded_model:
            return False

        loaded = str(loaded_model).strip().lower()

        loaded_name = Path(loaded).name.lower()
        loaded_stem = Path(loaded_name).stem.lower()

        aliases = self._model_aliases()

        for alias in aliases:

            alias_name = Path(alias).name.lower()
            alias_stem = Path(alias_name).stem.lower()

            if loaded_name == alias_name:
                return True

            if loaded_stem == alias_stem:
                return True

        # Strong worker-specific fallback.
        worker_keywords = {
            "general": ("qwen2.5-3b",),
            "coding": ("qwen2.5-coder-3b", "qwen2.5-coder"),
            "vision": ("qwen2.5-vl-3b", "qwen2.5-vl"),
            "document": ("gemma", "gemma3-4b"),
        }

        for keyword in worker_keywords.get(self.worker_type, ()):
            if keyword in loaded:
                return True

        return False

    # ============================================================
    # HTTP
    # ============================================================

    def _get_json(
        self,
        path: str,
        timeout: int = 5,
    ):
        request = urllib.request.Request(
            self.endpoint + path,
            method="GET",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout,
            ) as response:

                raw = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

                return json.loads(raw)

        except Exception:
            return None

    def _post_json(
        self,
        path: str,
        payload: dict,
        timeout: int = 240,
    ):

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.endpoint + path,
            data=data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout,
            ) as response:

                raw = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

                return json.loads(raw)

        except urllib.error.HTTPError as exc:

            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise RuntimeError(
                f"llama-server HTTP {exc.code}: {body}"
            ) from exc

    def _get_health(self) -> bool:

        result = self._get_json(
            "/health",
            timeout=3,
        )

        return (
            isinstance(result, dict)
            and result.get("status") == "ok"
        )

    def _get_loaded_model(self) -> Optional[str]:

        result = self._get_json(
            "/v1/models",
            timeout=5,
        )

        if not isinstance(result, dict):
            return None

        data = result.get("data")

        if not isinstance(data, list) or not data:
            return None

        first = data[0]

        if not isinstance(first, dict):
            return None

        model_id = first.get("id")

        if model_id:
            return str(model_id)

        return None

    def _endpoint_matches_requested_model(self) -> bool:
        loaded_model = self._get_loaded_model()

        return self._model_matches(
            loaded_model
        )

    # ============================================================
    # PROCESS / SERVER
    # ============================================================

    def load(
        self,
        model_path: Optional[str] = None,
        gpu_layers: int = -1,
    ) -> bool:

        if model_path:
            self.model_name = str(model_path)

        # --------------------------------------------------------
        # Already owned by this adapter.
        # --------------------------------------------------------

        if (
            self.process is not None
            and self.process.poll() is None
            and self._get_health()
            and self._endpoint_matches_requested_model()
        ):
            return True

        # --------------------------------------------------------
        # Existing server.
        #
        # Never reuse a server merely because /health is OK.
        # --------------------------------------------------------

        if self._get_health():

            loaded_model = self._get_loaded_model()

            if self._model_matches(loaded_model):
                self._external_server = True
                return True

            raise RuntimeError(
                "Dedicated model endpoint is already occupied by "
                "a different model. "
                f"worker={self.worker_type!r}, "
                f"endpoint={self.endpoint!r}, "
                f"requested={self.model_name!r}, "
                f"loaded={loaded_model!r}. "
                "Refusing cross-model reuse."
            )

        # --------------------------------------------------------
        # Start our own server.
        # --------------------------------------------------------

        if self.media_path:
            Path(
                self.media_path
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

        model_file = Path(
            str(self.model_name)
        ).expanduser()

        project_root = Path(
            __file__
        ).resolve().parents[2]

        if not model_file.is_absolute():
            model_file = (
                project_root
                / model_file
            )

        model_file = model_file.resolve()

        if not model_file.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_file}"
            )

        parsed = urllib.parse.urlparse(
            self.endpoint
        )

        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8080

        command = [
            LLAMA_SERVER,
            "-m",
            str(model_file),
            "--host",
            host,
            "--port",
            str(port),
            "-ngl",
            "999" if gpu_layers == -1 else str(gpu_layers),
            "-c",
            "4096",
        ]

        if self.mmproj_path:
            command.extend(
                [
                    "--mmproj",
                    self.mmproj_path,
                ]
            )

        if self.media_path:
            command.extend(
                [
                    "--media-path",
                    self.media_path,
                ]
            )

        if self.worker_type == "vision":
            command.extend(
                [
                    "--image-min-tokens",
                    "1024",
                ]
            )

        command.append(
            "--no-webui"
        )

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self._external_server = False

        deadline = time.time() + 120

        while time.time() < deadline:

            if self.process.poll() is not None:

                self.process = None

                raise RuntimeError(
                    f"llama-server exited during startup "
                    f"for worker={self.worker_type}."
                )

            if self._get_health():

                loaded_model = (
                    self._get_loaded_model()
                )

                if self._model_matches(
                    loaded_model
                ):
                    return True

                raise RuntimeError(
                    "llama-server started but model identity "
                    "verification failed. "
                    f"worker={self.worker_type!r}, "
                    f"requested={model_file.name!r}, "
                    f"loaded={loaded_model!r}."
                )

            time.sleep(0.5)

        raise TimeoutError(
            "Timed out waiting for llama-server: "
            f"{self.endpoint}"
        )

    def unload(self) -> bool:

        # Never kill an externally-owned process.
        if self._external_server:

            self._external_server = False
            self.process = None

            return True

        process = self.process

        self.process = None

        if process is None:
            return True

        try:

            process.terminate()
            process.wait(
                timeout=8
            )

        except Exception:

            try:
                process.kill()
            except Exception:
                pass

        return True

    def is_loaded(self) -> bool:

        if self._external_server:

            return (
                self._get_health()
                and self._endpoint_matches_requested_model()
            )

        return (
            self.process is not None
            and self.process.poll() is None
            and self._get_health()
            and self._endpoint_matches_requested_model()
        )

    # ============================================================
    # IMAGE
    # ============================================================

    def _prepare_local_image(
        self,
        image_path: str,
    ) -> str:

        source = (
            Path(image_path)
            .expanduser()
            .resolve()
        )

        if not source.exists():
            raise FileNotFoundError(
                f"Image not found: {source}"
            )

        if not source.is_file():
            raise ValueError(
                f"Image path is not a file: {source}"
            )

        # Also copy to media_path for logging / caching if configured
        if self.media_path:
            try:
                media_dir = Path(self.media_path)
                media_dir.mkdir(parents=True, exist_ok=True)
                destination = media_dir / f"{uuid.uuid4().hex}_{source.name}"
                shutil.copy2(source, destination)
            except Exception:
                pass

        # Use base64 Data URL (standard OpenAI / llama-server multimodal format)
        # This completely avoids filesystem permission, URI encoding (%20), or absolute path resolution issues in llama-server
        import base64
        import mimetypes

        mime_type, _ = mimetypes.guess_type(str(source))
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg"

        b64_content = base64.b64encode(source.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{b64_content}"

    # ============================================================
    # GENERATION
    # ============================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> WorkerInferenceResponse:

        if not self.is_loaded():
            self.load()

        image_path = kwargs.get(
            "image_path"
        )

        max_tokens = int(
            kwargs.get(
                "max_tokens",
                1024,
            )
        )

        temperature = float(
            kwargs.get(
                "temperature",
                0.2,
            )
        )

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": str(system_prompt),
                }
            )

        # --------------------------------------------------------
        # Text-only worker.
        # --------------------------------------------------------

        if not image_path:

            messages.append(
                {
                    "role": "user",
                    "content": str(prompt),
                }
            )

        # --------------------------------------------------------
        # Vision worker.
        # --------------------------------------------------------

        else:

            if self.worker_type != "vision":
                raise ValueError(
                    "image_path was supplied to "
                    "a non-vision worker."
                )

            image_url = (
                self._prepare_local_image(
                    str(image_path)
                )
            )

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": str(prompt),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            )

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self._post_json(
            "/v1/chat/completions",
            payload,
            timeout=240,
        )

        choices = response.get(
            "choices",
            [],
        )

        if not choices:
            raise RuntimeError(
                "Model returned no choices."
            )

        message = choices[0].get(
            "message",
            {},
        )

        content = message.get(
            "content",
            "",
        )

        if isinstance(content, list):

            pieces = []

            for item in content:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                if item.get("type") == "text":

                    pieces.append(
                        str(
                            item.get(
                                "text",
                                "",
                            )
                        )
                    )

            content = "\n".join(
                pieces
            )

        content = str(
            content or ""
        ).strip()

        if not content:

            reasoning = str(
                message.get(
                    "reasoning_content",
                    "",
                )
                or ""
            ).strip()

            if reasoning:
                content = reasoning

        if not content:
            raise RuntimeError(
                f"{self.worker_type} model returned "
                "an empty response."
            )

        usage = response.get(
            "usage",
            {},
        )

        completion_tokens = int(
            usage.get(
                "completion_tokens",
                0,
            )
            or 0
        )

        return WorkerInferenceResponse(
            worker_type=self.worker_type,
            status="success",
            content=content,
            tokens_generated=completion_tokens,
            error_message="",
        )

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Generator[str, None, None]:

        result = self.generate(
            prompt,
            system_prompt=system_prompt,
            **kwargs,
        )

        yield result.content

    # ============================================================
    # HEALTH
    # ============================================================

    def health(self):

        loaded_model = (
            self._get_loaded_model()
        )

        loaded = (
            self.is_loaded()
        )

        return {
            "worker": self.worker_type,
            "model": self.model_name,
            "loaded_model": loaded_model,
            "endpoint": self.endpoint,
            "loaded": loaded,
            "model_match": self._model_matches(
                loaded_model
            ),
            "vram_mb": self.vram_mb,
            "mmproj": self.mmproj_path,
            "media_path": self.media_path,
            "external_server": self._external_server,
        }

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, Optional

from model_manager.adapters.base import (
    BaseModelAdapter,
    WorkerInferenceResponse,
)


LLAMA_SERVER = "/home/piet/llama.cpp/build/bin/llama-server"


class LlamaCppAdapter(BaseModelAdapter):

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
        self.vram_mb = vram_mb
        self.mmproj_path = mmproj_path
        self.media_path = media_path
        self.process: Optional[subprocess.Popen] = None
        self.port = self._extract_port(self.endpoint)

    @staticmethod
    def _extract_port(endpoint: str) -> int:
        try:
            return int(endpoint.rsplit(":", 1)[1])
        except (ValueError, IndexError) as exc:
            raise ValueError(
                f"Invalid llama.cpp endpoint: {endpoint}"
            ) from exc

    def _health_url(self) -> str:
        return f"{self.endpoint}/health"

    def _chat_url(self) -> str:
        return f"{self.endpoint}/v1/chat/completions"

    def _wait_for_server(self, timeout: float = 60.0) -> bool:
        start = time.perf_counter()

        while time.perf_counter() - start < timeout:
            try:
                req = urllib.request.Request(
                    self._health_url(),
                    method="GET",
                )

                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        return True

            except Exception:
                pass

            time.sleep(0.5)

        return False

    def _post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        timeout: float = 300.0,
    ) -> Dict[str, Any]:

        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode(
                "utf-8",
                errors="replace",
            )
            raise RuntimeError(
                f"llama-server HTTP {exc.code}: {error_body}"
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach llama-server at {url}: {exc}"
            ) from exc

    # ================================================================
    # LIFECYCLE
    # ================================================================

    def load(self, model_path: Optional[str] = None) -> bool:

        if self.is_loaded():
            return True

        model_file = model_path or self.model_name
        self.model_name = model_file

        if not os.path.isfile(LLAMA_SERVER):
            raise FileNotFoundError(
                f"llama-server not found: {LLAMA_SERVER}"
            )

        if not os.path.isfile(model_file):
            raise FileNotFoundError(
                f"Model file not found: {model_file}"
            )

        cmd = [
            LLAMA_SERVER,
            "-m",
            model_file,
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "-ngl",
            "999",
            "-c",
            "4096",
            "--no-webui",
        ]

        if self.mmproj_path:

            if not os.path.isfile(self.mmproj_path):
                raise FileNotFoundError(
                    f"mmproj file not found: {self.mmproj_path}"
                )

            cmd.extend([
                "--mmproj",
                self.mmproj_path,
            ])

        if self.media_path:

            media_dir = os.path.abspath(
                os.path.expanduser(self.media_path)
            )

            os.makedirs(media_dir, exist_ok=True)

            cmd.extend([
                "--media-path",
                media_dir,
            ])

        if self.worker_type == "vision":
            cmd.extend([
                "--image-min-tokens",
                "1024",
            ])

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not self._wait_for_server():
            self.unload()

            raise RuntimeError(
                f"llama-server failed to start for worker "
                f"'{self.worker_type}' on port {self.port}"
            )

        return True

    def unload(self) -> bool:

        if self.process is None:
            return True

        if self.process.poll() is None:

            self.process.terminate()

            try:
                self.process.wait(timeout=10)

            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

        self.process = None

        return True

    def is_loaded(self) -> bool:
        return (
            self.process is not None
            and self.process.poll() is None
        )

    # ================================================================
    # VISION
    # ================================================================

    @staticmethod
    def _normalise_image_path(image_path: str) -> str:
        return os.path.abspath(
            os.path.expanduser(image_path)
        )

    def _prepare_image_reference(
        self,
        image_path: str,
    ) -> str:

        image_path = self._normalise_image_path(
            image_path
        )

        if not os.path.isfile(image_path):
            raise FileNotFoundError(
                f"Vision image does not exist: {image_path}"
            )

        if self.media_path:

            media_root = os.path.abspath(
                os.path.expanduser(self.media_path)
            )

            relative_path = os.path.relpath(
                image_path,
                media_root,
            )

            if relative_path.startswith(".."):
                raise ValueError(
                    f"Image must be inside media path: "
                    f"{media_root}"
                )

            # llama-server resolves file:// references relative to
            # --media-path. Never send an absolute path here.
            return f"file://{relative_path}"

        return f"file://{image_path}"

    # ================================================================
    # GENERATION
    # ================================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.2,
        **kwargs,
    ) -> WorkerInferenceResponse:

        try:

            if not self.is_loaded():
                self.load()

            image_path = kwargs.get("image_path")

            if image_path:

                if self.worker_type != "vision":
                    raise ValueError(
                        "image_path can only be used with "
                        "vision worker"
                    )

                image_url = self._prepare_image_reference(
                    image_path
                )

                user_content = [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ]

            else:
                user_content = prompt

            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt,
                })

            messages.append({
                "role": "user",
                "content": user_content,
            })

            payload = {
                "messages": messages,
                "max_tokens": int(max_tokens),
                "temperature": float(temperature),
                "stream": False,
            }

            started = time.perf_counter()

            response = self._post_json(
                self._chat_url(),
                payload,
            )

            latency_ms = (
                time.perf_counter() - started
            ) * 1000.0

            choices = response.get("choices", [])

            if not choices:
                raise RuntimeError(
                    f"llama-server returned no choices: "
                    f"{response}"
                )

            message = choices[0].get(
                "message",
                {},
            )

            output = message.get(
                "content",
                "",
            )

            if output is None:
                output = ""

            usage = response.get(
                "usage",
                {},
            )

            tokens_generated = usage.get(
                "completion_tokens",
                usage.get(
                    "output_tokens",
                    0,
                ),
            )

            return WorkerInferenceResponse(
                worker_type=self.worker_type,
                status="success",
                content=str(output),
                structured_data=None,
                tokens_generated=int(
                    tokens_generated or 0
                ),
                latency_ms=round(
                    latency_ms,
                    2,
                ),
                vram_used_mb=self.vram_mb,
                error_message="",
            )

        except Exception as exc:

            return WorkerInferenceResponse(
                worker_type=self.worker_type,
                status="failed",
                content="",
                structured_data=None,
                tokens_generated=0,
                latency_ms=0.0,
                vram_used_mb=self.vram_mb,
                error_message=str(exc),
            )

    # ================================================================
    # STREAM
    # ================================================================

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.2,
        **kwargs,
    ) -> Iterator[str]:

        result = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        yield result.content

    # ================================================================
    # HEALTH
    # ================================================================

    def health(self) -> Dict[str, Any]:

        return {
            "worker_type": self.worker_type,
            "model": self.model_name,
            "endpoint": self.endpoint,
            "loaded": self.is_loaded(),
            "vram_mb": self.vram_mb,
            "mmproj": self.mmproj_path,
            "media_path": self.media_path,
        }

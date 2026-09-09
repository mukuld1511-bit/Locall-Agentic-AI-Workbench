import time
from typing import Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from model_manager.adapters.base import BaseModelAdapter, WorkerInferenceResponse


class TransformersOrganizerAdapter(BaseModelAdapter):
    """
    Local Transformers adapter for the trained Organizer safetensors model.

    Unlike GGUF workers, the Organizer is loaded directly from a local
    Hugging Face/Transformers-compatible directory.
    """

    def __init__(
        self,
        worker_type: str,
        model_name: str,
        model_path: str,
    ):
        self.worker_type = worker_type
        self.model_name = model_name
        self.model_path = model_path

        self.tokenizer = None
        self.model = None
        self._loaded = False

    def load(self, file_path: str = "") -> bool:
        path = file_path or self.model_path

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(path)

            dtype = (
                torch.bfloat16
                if torch.cuda.is_available()
                else torch.float32
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                path,
                dtype=dtype,
            )

            if torch.cuda.is_available():
                self.model = self.model.to("cuda")

            self.model.eval()
            self._loaded = True
            return True

        except Exception:
            self.tokenizer = None
            self.model = None
            self._loaded = False
            return False

    def unload(self) -> None:
        self.model = None
        self.tokenizer = None
        self._loaded = False

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def is_loaded(self) -> bool:
        return self._loaded and self.model is not None and self.tokenizer is not None

    def health(self) -> dict:
        """Return local readiness/health information."""
        return {
            "healthy": self.is_loaded(),
            "loaded": self.is_loaded(),
            "worker_type": self.worker_type,
            "model_name": self.model_name,
        }

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """Minimal streaming-compatible wrapper.

        The first production integration uses non-streaming generation.
        This method satisfies the adapter contract and yields the final
        response as a single chunk.
        """
        response = self.generate(
            prompt,
            system_prompt,
            **kwargs,
        )

        yield response

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> WorkerInferenceResponse:

        if not self.is_loaded():
            return WorkerInferenceResponse(
                worker_type=self.worker_type,
                status="error",
                content="",
                error_message="Organizer model is not loaded.",
            )

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        try:
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

            device = next(self.model.parameters()).device

            inputs = self.tokenizer(
                text,
                return_tensors="pt",
            ).to(device)

            max_new_tokens = int(kwargs.get("max_new_tokens", 400))

            start = time.time()

            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                )

            latency_ms = (time.time() - start) * 1000.0

            generated = output[0][inputs["input_ids"].shape[1]:]

            answer = self.tokenizer.decode(
                generated,
                skip_special_tokens=True,
            )

            token_count = int(generated.shape[-1])

            return WorkerInferenceResponse(
                worker_type=self.worker_type,
                status="success",
                content=answer,
                error_message="",
                tokens_generated=token_count,
                latency_ms=latency_ms,
            )

        except Exception as exc:
            return WorkerInferenceResponse(
                worker_type=self.worker_type,
                status="error",
                content="",
                error_message=str(exc),
            )

from pathlib import Path
from typing import Any

from PIL import Image

from .api import ImageResponse, PictorAPIError


class LocalImageProvider:
    """Generate and restyle images locally with Hugging Face Diffusers."""

    def __init__(self, model_id: str, output_dir: Path, device: str = "auto"):
        try:
            import torch
            from diffusers import StableDiffusionImg2ImgPipeline
            from diffusers import StableDiffusionPipeline
        except ImportError as exc:
            raise PictorAPIError(
                "Локальные зависимости не установлены. Выполните "
                "pip install -r requirements.txt."
            ) from exc

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.output_dir = output_dir
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        try:
            self.text_pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                safety_checker=None,
            )
            self.text_pipe.to(device)
            self.edit_pipe: StableDiffusionImg2ImgPipeline | None = None
            self.device = device
            self.model_id = model_id
        except Exception as exc:
            raise PictorAPIError(
                "Не удалось загрузить локальную модель. Проверьте интернет "
                "при первом запуске и свободное место на диске."
            ) from exc

    def generate(self, prompt: str) -> ImageResponse:
        try:
            prompt = self._fit_prompt(prompt)
            result = self.text_pipe(
                prompt=prompt,
                guidance_scale=7.5,
                num_inference_steps=20,
            )
            return ImageResponse(data=self._encode_png(result.images[0]))
        except Exception as exc:
            raise PictorAPIError(
                f"Локальная генерация завершилась с ошибкой "
                f"({type(exc).__name__}): {exc}"
            ) from exc

    def restyle(self, image_path: Path, prompt: str) -> ImageResponse:
        try:
            from diffusers import StableDiffusionImg2ImgPipeline

            prompt = self._fit_prompt(prompt)
            if self.edit_pipe is None:
                import torch

                torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
                self.edit_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=torch_dtype,
                    safety_checker=None,
                )
                self.edit_pipe.to(self.device)

            source = Image.open(image_path).convert("RGB")
            source.thumbnail((512, 512), Image.Resampling.LANCZOS)
            result = self.edit_pipe(
                prompt=prompt,
                image=source,
                strength=0.75,
                guidance_scale=7.5,
                num_inference_steps=20,
            )
            return ImageResponse(data=self._encode_png(result.images[0]))
        except Exception as exc:
            raise PictorAPIError(
                f"Локальная перерисовка завершилась с ошибкой "
                f"({type(exc).__name__}): {exc}"
            ) from exc

    def _fit_prompt(self, prompt: str) -> str:
        tokens = self.text_pipe.tokenizer(
            prompt,
            truncation=True,
            max_length=self.text_pipe.tokenizer.model_max_length,
            return_tensors="pt",
        )
        return self.text_pipe.tokenizer.decode(
            tokens.input_ids[0],
            skip_special_tokens=True,
        )

    @staticmethod
    def _encode_png(image: Image.Image) -> bytes:
        import io

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

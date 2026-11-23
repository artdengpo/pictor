from pathlib import Path

from PIL import Image

from .api import ImageResponse, PictorAPIError


class LocalImageProvider:
    """Generate images locally with Hugging Face Diffusers."""

    def __init__(self, model_id: str, output_dir: Path, device: str = "auto"):
        try:
            import torch
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
            self.device = device
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

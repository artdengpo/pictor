import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from .config import Settings


class PictorAPIError(RuntimeError):
    """A safe, user-facing API error that never includes secret values."""


@dataclass(frozen=True)
class ImageResponse:
    data: bytes


class PictorClient:
    """OpenAI Images API wrapper."""

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise PictorAPIError(
                "Не задан API-ключ. Создайте файл .env рядом с проектом "
                "и запишите OPENAI_API_KEY=ваш_ключ."
            )
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    @property
    def output_dir(self) -> Path:
        return self.settings.output_dir

    def generate(self, prompt: str) -> ImageResponse:
        try:
            response = self.client.images.generate(
                model=self.settings.image_model,
                prompt=prompt,
                size=self.settings.image_size,
            )
            return ImageResponse(data=self._extract_image(response))
        except Exception as exc:
            raise self._translate_error(exc) from exc

    @staticmethod
    def _extract_image(response: Any) -> bytes:
        if not getattr(response, "data", None):
            raise PictorAPIError("API не вернул изображение.")

        item = response.data[0]
        if getattr(item, "b64_json", None):
            return base64.b64decode(item.b64_json)
        if getattr(item, "url", None):
            try:
                with urlopen(item.url, timeout=60) as downloaded:
                    return downloaded.read()
            except Exception as exc:
                raise PictorAPIError("Не удалось скачать сгенерированное изображение.") from exc
        raise PictorAPIError("Ответ API не содержит данные изображения.")

    @staticmethod
    def _translate_error(error: Exception) -> PictorAPIError:
        if isinstance(error, PictorAPIError):
            return error
        if isinstance(error, (APITimeoutError, APIConnectionError)):
            return PictorAPIError(
                "Не удалось подключиться к API. Проверьте интернет-соединение и повторите попытку."
            )
        if isinstance(error, RateLimitError):
            return PictorAPIError(
                "Превышен лимит API или закончился баланс. Проверьте аккаунт OpenAI и попробуйте позже."
            )
        if isinstance(error, APIStatusError):
            status = getattr(error, "status_code", None)
            if status in (401, 403):
                return PictorAPIError(
                    "API-ключ недействителен или не имеет доступа к этой модели."
                )
            if status == 400:
                return PictorAPIError(
                    "API отклонил запрос. Попробуйте изменить описание или размер изображения."
                )
            if status and 500 <= status < 600:
                return PictorAPIError(
                    "Сервис OpenAI временно недоступен. Повторите попытку чуть позже."
                )
            return PictorAPIError(
                "API вернул ошибку. Проверьте ключ, баланс, лимиты и повторите запрос."
            )
        message = str(error).strip()
        if message:
            return PictorAPIError(
                "Не удалось выполнить запрос к API. Повторите попытку или проверьте настройки."
            )
        return PictorAPIError("Произошла неизвестная ошибка при обращении к API.")

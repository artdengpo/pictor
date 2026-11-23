from typing import Final


SUPPORTED_LANGUAGES: Final[dict[str, str]] = {
    "ru": "Русский",
    "en": "English",
}


def detect_language(text: str) -> str:
    """Return the detected language code; Russian has Cyrillic priority."""

    if not text:
        return "en"

    cyrillic_count = sum("А" <= char.upper() <= "Я" or char.lower() in "ё" for char in text)
    latin_count = sum(char.isascii() and char.isalpha() for char in text)

    if cyrillic_count > latin_count:
        return "ru"
    if cyrillic_count:
        return "ru"
    return "en"


def enhance_prompt(text: str) -> str:
    """Add tasteful quality instructions while preserving the user's intent."""

    language = detect_language(text)
    if language == "ru":
        return (
            f"Создай высококачественное и цельное изображение: {text.strip()}. "
            "Используй продуманную композицию, естественный свет, аккуратные детали "
            "и приятную цветовую палитру. Без водяных знаков и лишнего текста."
        )

    return (
        f"Create a high-quality, cohesive image of: {text.strip()}. "
        "Use thoughtful composition, natural lighting, polished details, "
        "and a harmonious color palette. No watermarks or unrelated text."
    )


def build_restyle_prompt(style_description: str) -> str:
    """Build a restyling prompt that protects subject recognition."""

    language = detect_language(style_description)
    if language == "ru":
        return (
            f"Перерисуй фотографию в следующем художественном стиле: {style_description.strip()}. "
            "Сохрани узнаваемые персонажей, предметы, позу и основной сюжет; "
            "изменяй технику рисования, текстуры и палитру. Без подписи, водяного знака "
            "или постороннего текста."
        )

    return (
        f"Redraw the photograph in this artistic style: {style_description.strip()}. "
        "Preserve recognizable subjects, objects, pose, and the main composition; "
        "change the rendering technique, textures, and palette. "
        "No signature, watermark, or unrelated text."
    )

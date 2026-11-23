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
    """Build a concise English style prompt while protecting image content."""

    style = style_description.strip()
    if detect_language(style) == "ru":
        normalized = style.lower()
        translations = (
            (("акварел",), "soft watercolor illustration"),
            (("карандаш", "скетч"), "gentle pencil sketch"),
            (("аниме",), "subtle anime illustration"),
            (("маслян", "масля"), "soft oil painting"),
            (("киберпанк", "неонов"), "subtle neon cyberpunk color grading"),
            (("ван гог", "вангог"), "subtle post-impressionist brushwork"),
        )
        style = next(
            (
                english
                for keywords, english in translations
                if any(keyword in normalized for keyword in keywords)
            ),
            "subtle artistic color and texture treatment",
        )

    return (
        f"Apply {style} to the input photo. Keep the exact same person, face, "
        "clothing, objects, pose, proportions, and composition. Do not replace, "
        "add, remove, or reshape anything. Make only a subtle change to the "
        "rendering texture and colors. Preserve the original photo's details."
    )

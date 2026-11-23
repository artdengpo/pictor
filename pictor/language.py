import re
from typing import Final


SUPPORTED_LANGUAGES: Final[dict[str, str]] = {
    "ru": "Русский",
    "en": "English",
}

ART_STYLES: Final[dict[str, tuple[str, str]]] = {
    "1": ("Масляная живопись", "oil painting"),
    "2": ("Акварель", "watercolor painting"),
    "3": ("Реалистичная цифровая картина", "realistic digital painting"),
    "4": ("Аниме", "anime illustration"),
    "5": ("Карандашный рисунок", "pencil drawing"),
}

_RU_TO_EN: Final[dict[str, str]] = {
    "нарисуй": "",
    "нарисовать": "",
    "создай": "",
    "создать": "",
    "изобрази": "",
    "изобразить": "",
    "покажи": "",
    "мне": "",
    "пожалуйста": "",
    "на": "on",
    "в": "in",
    "с": "with",
    "и": "and",
    "под": "under",
    "над": "above",
    "у": "near",
    "около": "near",
    "красная": "red",
    "красный": "red",
    "красную": "red",
    "красное": "red",
    "красные": "red",
    "синяя": "blue",
    "синий": "blue",
    "синюю": "blue",
    "синее": "blue",
    "зеленая": "green",
    "зелёная": "green",
    "зеленый": "green",
    "зелёный": "green",
    "зеленую": "green",
    "зелёную": "green",
    "желтая": "yellow",
    "желтую": "yellow",
    "желтый": "yellow",
    "белая": "white",
    "белый": "white",
    "белую": "white",
    "черная": "black",
    "чёрная": "black",
    "черный": "black",
    "чёрный": "black",
    "маленькая": "small",
    "маленький": "small",
    "большая": "large",
    "большой": "large",
    "красивая": "beautiful",
    "красивый": "beautiful",
    "яркая": "vibrant",
    "яркий": "vibrant",
    "старинный": "old-fashioned",
    "винтажный": "vintage",
    "спортивная": "sports",
    "спортивную": "sports",
    "спортивный": "sports",
    "современная": "modern",
    "современный": "modern",
    "цветок": "flower",
    "цветы": "flowers",
    "цветов": "flowers",
    "букет": "bouquet",
    "пионы": "peonies",
    "пионов": "peonies",
    "пион": "peony",
    "розы": "roses",
    "роз": "roses",
    "роза": "rose",
    "тюльпаны": "tulips",
    "тюльпан": "tulip",
    "машина": "car",
    "машину": "car",
    "машины": "cars",
    "машиной": "car",
    "автомобиль": "car",
    "автомобиля": "car",
    "автомобилем": "car",
    "авто": "car",
    "огурец": "cucumber",
    "огурца": "cucumber",
    "огурцы": "cucumbers",
    "кот": "cat",
    "кота": "cat",
    "кошка": "cat",
    "кошку": "cat",
    "собака": "dog",
    "собаку": "dog",
    "пес": "dog",
    "пёс": "dog",
    "дом": "house",
    "дома": "house",
    "замок": "castle",
    "дерево": "tree",
    "деревья": "trees",
    "лес": "forest",
    "горы": "mountains",
    "гора": "mountain",
    "море": "sea",
    "океан": "ocean",
    "город": "city",
    "улица": "street",
    "дорога": "road",
    "небо": "sky",
    "солнце": "sun",
    "луна": "moon",
    "звезды": "stars",
    "звёзды": "stars",
    "дождь": "rain",
    "снег": "snow",
    "фон": "background",
    "белом": "white",
    "светлом": "light",
    "темном": "dark",
    "тёмном": "dark",
    "столе": "table",
    "дороге": "road",
    "дождём": "rain",
    "дождем": "rain",
    "дождя": "rain",
    "дожде": "rain",
    "стиле": "style",
    "пейзаж": "landscape",
    "реалистично": "realistic",
    "реалистичный": "realistic",
    "детализированная": "detailed",
    "детализированный": "detailed",
    "акварелью": "in watercolor",
    "маслом": "in oil paint",
    "аниме": "anime",
    "карандашом": "in pencil",
    "живопись": "painting",
    "живописный": "painterly",
    "мультяшный": "cartoon",
    "милый": "cute",
    "грустный": "sad",
    "ночью": "at night",
    "ночной": "nighttime",
    "утром": "in the morning",
    "закат": "sunset",
    "рассвет": "sunrise",
    "мягкий": "soft",
    "свет": "light",
}

_PHRASES: Final[tuple[tuple[str, str], ...]] = (
    ("на белом фоне", "on a plain white background"),
    ("на светлом фоне", "on a light background"),
    ("на темном фоне", "on a dark background"),
    ("на тёмном фоне", "on a dark background"),
    ("в стиле аниме", "in anime style"),
    ("масляной живописью", "as an oil painting"),
    ("в старом городе", "in an old town"),
)

_WORD_PATTERN = re.compile(r"[А-Яа-яЁё]+|[A-Za-z]+|\d+|[^\w\s]", re.UNICODE)


def detect_language(text: str) -> str:
    """Return the detected language code; Cyrillic input is treated as Russian."""

    if not text:
        return "en"

    if any("А" <= char.upper() <= "Я" or char.lower() == "ё" for char in text):
        return "ru"
    return "en"


def translate_russian_prompt(text: str) -> str:
    """Translate common Russian prompt words locally, without a network service."""

    if detect_language(text) != "ru":
        return text.strip()

    translated = text.lower()
    for source, target in _PHRASES:
        translated = translated.replace(source, f" {target} ")

    parts = _WORD_PATTERN.findall(translated)
    result: list[str] = []
    for part in parts:
        if part in _RU_TO_EN:
            replacement = _RU_TO_EN[part]
            if replacement:
                result.append(replacement)
        else:
            result.append(part)

    prompt = " ".join(result)
    prompt = re.sub(r"\s+([,.!?])", r"\1", prompt)
    prompt = re.sub(r"\s+", " ", prompt).strip(" ,.")
    return prompt


def build_generation_prompt(subject: str, style: str) -> str:
    """Build a compact English prompt with the main subject up front."""

    translated_subject = translate_russian_prompt(subject)
    translated_style = translate_russian_prompt(style)
    return (
        f"Create one clear image of {translated_subject}. "
        f"Art style: {translated_style}. "
        "Keep the described subject prominent. No unrelated objects, text, or watermark."
    )


def enhance_prompt(text: str) -> str:
    """Preserve the public helper while translating common Russian prompt words."""

    translated = translate_russian_prompt(text)
    return (
        f"Create one clear, detailed image of {translated}. "
        "Keep the main subject prominent. No unrelated objects, text, or watermark."
    )

import re
import unicodedata
from datetime import datetime
from pathlib import Path

CYRILLIC_TRANSLITERATION = str.maketrans(
    {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
)


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def make_slug(text: str, max_length: int = 48) -> str:
    """Create a compact, filesystem-safe filename stem."""

    text = text.lower().translate(CYRILLIC_TRANSLITERATION)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:max_length].rstrip("_") or "artwork"


def unique_output_path(output_dir: Path, stem: str, suffix: str = ".png") -> Path:
    """Reserve a non-existing filename by adding a numeric suffix."""

    ensure_output_dir(output_dir)
    candidate = output_dir / f"{stem}{suffix}"
    number = 2
    while candidate.exists():
        candidate = output_dir / f"{stem}_{number}{suffix}"
        number += 1
    return candidate


def generate_output_path(output_dir: Path, prompt: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    stem = f"{timestamp}_{make_slug(prompt)}"
    return unique_output_path(output_dir, stem)


def save_png(response_data: bytes, destination: Path) -> Path:
    ensure_output_dir(destination.parent)
    destination.write_bytes(response_data)
    return destination


def list_output_files(output_dir: Path) -> list[tuple[Path, datetime, int]]:
    if not output_dir.exists():
        return []

    supported = {".png", ".jpg", ".jpeg", ".webp"}
    records: list[tuple[Path, datetime, int]] = []
    for path in output_dir.iterdir():
        if path.is_file() and path.suffix.lower() in supported:
            modified = datetime.fromtimestamp(path.stat().st_mtime)
            records.append((path, modified, path.stat().st_size))
    return sorted(records, key=lambda record: record[1], reverse=True)

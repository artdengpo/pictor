import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    openai_api_key: str
    image_model: str
    image_size: str
    output_dir: Path
    provider: str
    local_model: str
    local_device: str


def load_settings(project_root: Path | None = None) -> Settings:
    """Load .env and environment variables without printing any secrets."""

    root = project_root or Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        image_model=os.getenv("PICTOR_IMAGE_MODEL", "gpt-image-1").strip()
        or "gpt-image-1",
        image_size=os.getenv("PICTOR_IMAGE_SIZE", "1024x1024").strip()
        or "1024x1024",
        output_dir=root / "output",
        provider=os.getenv("PICTOR_PROVIDER", "local").strip().lower() or "local",
        local_model=os.getenv(
            "PICTOR_LOCAL_MODEL", "runwayml/stable-diffusion-v1-5"
        ).strip()
        or "runwayml/stable-diffusion-v1-5",
        local_device=os.getenv("PICTOR_LOCAL_DEVICE", "auto").strip().lower()
        or "auto",
    )

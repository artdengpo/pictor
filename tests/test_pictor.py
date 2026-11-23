from pathlib import Path

from PIL import Image

from pictor.images import generate_output_path, make_slug, restyled_output_path, validate_image
from pictor.language import detect_language, enhance_prompt, build_restyle_prompt
from pictor.local_provider import LocalImageProvider


def test_detects_cyrillic() -> None:
    assert detect_language("букет пионов акварелью") == "ru"
    assert detect_language("a watercolor bouquet") == "en"


def test_enhances_prompt_in_detected_language() -> None:
    russian = enhance_prompt("пионы")
    english = enhance_prompt("peonies")
    assert "Создай" in russian
    assert "Create" in english


def test_restyle_prompt_preserves_subject() -> None:
    assert "узнаваем" in build_restyle_prompt("акварель")
    assert "recognizable" in build_restyle_prompt("watercolor")


def test_make_slug_is_safe() -> None:
    slug = make_slug("Грустный кот / под дождём")
    assert slug
    assert "/" not in slug
    assert all(char.isascii() or char.isdigit() for char in slug)


def test_output_paths_have_timestamp_and_unique_suffix(tmp_path: Path) -> None:
    first = generate_output_path(tmp_path, "peonies")
    first.write_bytes(b"test")
    second = generate_output_path(tmp_path, "peonies")
    assert first != second
    assert first.name.startswith("20")
    assert second.name.endswith(".png")


def test_restyled_output_path(tmp_path: Path) -> None:
    path = restyled_output_path(tmp_path, Path("my-photo.jpg"))
    assert path.name.startswith("restyled_my_photo_")


def test_validates_real_image(tmp_path: Path) -> None:
    source = tmp_path / "photo.png"
    Image.new("RGB", (32, 32), "white").save(source)
    assert validate_image(source).size == (32, 32)


def test_rejects_non_image(tmp_path: Path) -> None:
    source = tmp_path / "not-an-image.txt"
    source.write_text("hello", encoding="utf-8")
    try:
        validate_image(source)
    except ValueError as exc:
        assert "не является" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_local_provider_returns_cli_compatible_image_response() -> None:
    class FakeTokenizer:
        model_max_length = 77

        def __call__(self, prompt, **kwargs):
            return type("Tokens", (), {"input_ids": [[1, 2, 3]]})()

        def decode(self, tokens, **kwargs):
            return "flowers"

    class FakePipeline:
        tokenizer = FakeTokenizer()

        def __call__(self, **kwargs):
            return type("Result", (), {"images": [Image.new("RGB", (4, 4), "pink")]})()

    provider = LocalImageProvider.__new__(LocalImageProvider)
    provider.text_pipe = FakePipeline()
    result = provider.generate("цветы")

    assert result.data.startswith(b"\x89PNG\r\n\x1a\n")

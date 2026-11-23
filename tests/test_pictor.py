import io
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from pictor.cli import generate_artwork, print_menu
from pictor.images import generate_output_path, make_slug
from pictor.language import (
    build_generation_prompt,
    detect_language,
    enhance_prompt,
    translate_russian_prompt,
)
from pictor.local_provider import LocalImageProvider


def test_detects_cyrillic() -> None:
    assert detect_language("букет пионов акварелью") == "ru"
    assert detect_language("a watercolor bouquet") == "en"


def test_enhances_prompt_in_english() -> None:
    russian = enhance_prompt("пионы")
    english = enhance_prompt("peonies")
    assert "peonies" in russian
    assert "Create" in english


def test_russian_car_prompt_translates_main_subject() -> None:
    translated = translate_russian_prompt("Нарисуй красную спортивную машину")
    assert "car" in translated
    assert "red" in translated
    assert "cucumber" not in translated


def test_generation_prompt_puts_subject_before_style() -> None:
    prompt = build_generation_prompt("машину", "watercolor painting")
    assert prompt.index("car") < prompt.index("Art style")
    assert "watercolor painting" in prompt
    assert "unrelated objects" in prompt


def test_generate_artwork_uses_translated_subject_and_saves_image(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    class FakeClient:
        output_dir = tmp_path

        def generate(self, prompt: str):
            self.prompt = prompt
            image_buffer = io.BytesIO()
            Image.new("RGB", (4, 4), "red").save(image_buffer, format="PNG")
            return SimpleNamespace(data=image_buffer.getvalue())

    answers = iter(("Нарисуй красную машину", "3"))
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    client = FakeClient()

    generate_artwork(client)

    assert "red car" in client.prompt
    assert "cucumber" not in client.prompt
    assert len(list(tmp_path.glob("*.png"))) == 1
    assert "Картина сохранена" in capsys.readouterr().out


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


def test_menu_contains_generation_history_and_exit_only(capsys) -> None:
    print_menu()
    menu = capsys.readouterr().out
    assert "Нарисовать по описанию" in menu
    assert "История" in menu
    assert "Выход" in menu
    assert "Перерисовать" not in menu

from pathlib import Path

from .api import PictorAPIError, PictorClient
from .config import load_settings
from .images import (
    generate_output_path,
    list_output_files,
    prepare_image,
    restyled_output_path,
    save_png,
)
from .language import build_restyle_prompt, enhance_prompt
from .local_provider import LocalImageProvider


def print_menu() -> None:
    print("\n================ Pictor ================")
    print("1. Нарисовать по описанию")
    print("2. Перерисовать моё фото")
    print("3. История")
    print("4. Выход")
    print("========================================")


def read_non_empty(prompt: str) -> str | None:
    value = input(prompt).strip()
    if not value:
        print("Пустое значение не подходит. Введите хотя бы один символ.")
        return None
    return value


def normalize_photo_path(value: str) -> Path:
    """Accept paths pasted with matching surrounding quotes."""

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return Path(value).expanduser()


def generate_artwork(client: PictorClient | LocalImageProvider) -> None:
    prompt = read_non_empty("Что нарисовать? ")
    if prompt is None:
        return

    print("Генерирую изображение…")
    try:
        enhanced = enhance_prompt(prompt)
        response = client.generate(enhanced)
        destination = generate_output_path(client.output_dir, prompt)
        saved = save_png(response.data, destination)
        print(f"Готово: {saved}")
    except PictorAPIError as exc:
        print(f"Не удалось: {exc}")
    except OSError:
        print("Не удалось сохранить файл. Проверьте права на запись в папку output.")
    except Exception as exc:
        print(
            "Не удалось выполнить генерацию "
            f"({type(exc).__name__}): {exc}"
        )


def restyle_photo(client: PictorClient | LocalImageProvider) -> None:
    path_text = read_non_empty("Укажите путь к фотографии: ")
    if path_text is None:
        return

    source = normalize_photo_path(path_text)
    try:
        prepared_path, prepared_image = prepare_image(source)
    except FileNotFoundError as exc:
        print(f"Не удалось: {exc}. Проверьте путь и попробуйте ещё раз.")
        return
    except ValueError as exc:
        print(f"Не удалось: {exc}")
        return
    except Exception:
        print("Не удалось открыть файл изображения.")
        return

    style = read_non_empty("Опишите желаемый стиль: ")
    if style is None:
        prepared_image.close()
        prepared_path.unlink(missing_ok=True)
        return

    print("Перерисовываю фотографию…")
    try:
        prompt = build_restyle_prompt(style)
        response = client.restyle(prepared_path, prompt)
        destination = restyled_output_path(client.output_dir, source)
        saved = save_png(response.data, destination)
        print(f"Готово: {saved}")
    except PictorAPIError as exc:
        print(f"Не удалось: {exc}")
    except OSError:
        print("Не удалось сохранить результат. Проверьте права на запись в папку output.")
    except Exception:
        print("Не удалось выполнить перерисовку. Проверьте изображение и повторите попытку.")
    finally:
        prepared_image.close()
        prepared_path.unlink(missing_ok=True)


def show_history() -> None:
    settings = load_settings()
    records = list_output_files(settings.output_dir)
    print("\nИстория сгенерированных изображений:")
    if not records:
        print("Пока нет файлов. Сначала нарисуйте картинку или перерисуйте фото.")
        return

    for path, modified, size in records:
        date_text = modified.strftime("%Y-%m-%d %H:%M")
        size_text = f"{size / 1024:.1f} КБ"
        print(f"- {date_text} | {size_text} | {path}")


def main() -> None:
    settings = load_settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if settings.provider == "local":
            print("Используется бесплатная локальная модель.")
            print("Первый запуск скачает модель; затем работа станет независимой от API.")
            client: PictorClient | LocalImageProvider = LocalImageProvider(
                settings.local_model,
                settings.output_dir,
                settings.local_device,
            )
        elif settings.provider == "openai":
            client = PictorClient(settings)
        else:
            print(
                "Неизвестный PICTOR_PROVIDER. Используйте local или openai "
                "в файле .env."
            )
            return
    except PictorAPIError as exc:
        print(exc)
        return

    while True:
        print_menu()
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            generate_artwork(client)
        elif choice == "2":
            restyle_photo(client)
        elif choice == "3":
            show_history()
        elif choice == "4":
            print("До встречи!")
            return
        else:
            print("Такого пункта нет. Введите число от 1 до 4.")

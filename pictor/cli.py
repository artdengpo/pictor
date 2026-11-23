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


def generate_artwork(client: PictorClient) -> None:
    prompt = read_non_empty("Что нарисовать? ")
    if prompt is None:
        return

    print("Генерирую изображение…")
    try:
        enhanced = enhance_prompt(prompt)
        response = client.generate(enhanced)
        destination = generate_output_path(client.settings.output_dir, prompt)
        saved = save_png(response.data, destination)
        print(f"Готово: {saved}")
    except PictorAPIError as exc:
        print(f"Не удалось: {exc}")
    except OSError:
        print("Не удалось сохранить файл. Проверьте права на запись в папку output.")
    except Exception:
        print("Не удалось выполнить генерацию. Повторите попытку с другим описанием.")


def restyle_photo(client: PictorClient) -> None:
    path_text = read_non_empty("Укажите путь к фотографии: ")
    if path_text is None:
        return

    source = Path(path_text).expanduser()
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
        destination = restyled_output_path(client.settings.output_dir, source)
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

    if not settings.openai_api_key:
        print("Pictor не запущен: не задан API-ключ.")
        print("Создайте файл .env рядом с проектом и укажите:")
        print("OPENAI_API_KEY=ваш_ключ")
        print("Где взять ключ: https://platform.openai.com/api-keys")
        return

    try:
        client = PictorClient(settings)
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

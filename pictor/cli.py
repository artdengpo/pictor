import sys

from .api import PictorAPIError, PictorClient
from .config import load_settings
from .images import (
    generate_output_path,
    list_output_files,
    save_png,
)
from .language import ART_STYLES, build_generation_prompt
from .local_provider import LocalImageProvider


def _styled(text: str, color: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{color}m{text}\033[0m"


def print_menu() -> None:
    print()
    print(_styled("╭──────────────────────────────────────────╮", "36"))
    print(_styled("│            P I C T O R                   │", "35"))
    print(_styled("│       Ваша идея — ваша картина           │", "36"))
    print(_styled("├──────────────────────────────────────────┤", "36"))
    print("│  1. Нарисовать по описанию                │")
    print("│  2. История                               │")
    print("│  3. Выход                                 │")
    print(_styled("╰──────────────────────────────────────────╯", "36"))


def choose_art_style() -> str | None:
    print("\nВыберите стиль:")
    for number, (label, _) in ART_STYLES.items():
        print(f"  {number}. {label}")
    print("  6. Свой стиль")

    choice = input("Стиль [1–6]: ").strip()
    if choice in ART_STYLES:
        return ART_STYLES[choice][1]
    if choice == "6":
        return read_non_empty("Опишите стиль на русском или английском: ")

    print("Такого стиля нет. Выберите число от 1 до 6.")
    return None


def read_non_empty(prompt: str) -> str | None:
    value = input(prompt).strip()
    if not value:
        print("Пустое значение не подходит. Введите хотя бы один символ.")
        return None
    return value


def generate_artwork(client: PictorClient | LocalImageProvider) -> None:
    subject = read_non_empty(
        "Что нарисовать? Сначала назовите главный объект (например: машина, букет пионов): "
    )
    if subject is None:
        return

    style = choose_art_style()
    if style is None:
        return

    prompt = build_generation_prompt(subject, style)
    print(_styled(f"\nПромт модели: {prompt}", "36"))
    print(_styled("Генерирую изображение. На CPU это может занять несколько минут…", "33"))
    try:
        response = client.generate(prompt)
        destination = generate_output_path(client.output_dir, subject)
        saved = save_png(response.data, destination)
        print(_styled(f"Готово! Картина сохранена: {saved}", "32"))
    except PictorAPIError as exc:
        print(_styled(f"Не удалось создать картину: {exc}", "31"))
    except OSError:
        print(_styled(
            "Не удалось сохранить файл. Проверьте права на запись в папку output.",
            "31",
        ))
    except Exception as exc:
        print(
            _styled(
                f"Не удалось выполнить генерацию ({type(exc).__name__}): {exc}",
                "31",
            )
        )


def show_history() -> None:
    settings = load_settings()
    records = list_output_files(settings.output_dir)
    print("\nИстория сгенерированных изображений:")
    if not records:
        print("Пока нет картин. Сначала нарисуйте что-нибудь по описанию.")
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
            print(_styled("Pictor работает на бесплатной локальной модели.", "32"))
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
            show_history()
        elif choice == "3":
            print("До встречи!")
            return
        else:
            print("Такого пункта нет. Введите число от 1 до 3.")

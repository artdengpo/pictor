import threading
from pathlib import Path
from typing import Callable

import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from .api import PictorAPIError, PictorClient
from .config import Settings, load_settings
from .images import generate_output_path, list_output_files, save_png
from .language import ART_STYLES, build_generation_prompt
from .local_provider import LocalImageProvider


BACKGROUND = "#11131B"
SIDEBAR = "#171A25"
SURFACE = "#1D2230"
SURFACE_LIGHT = "#252B3A"
TEXT = "#F4F2EF"
MUTED = "#9BA3B5"
ACCENT = "#B99AF7"
ACCENT_HOVER = "#CBB5FF"
SUCCESS = "#80D6AE"
DANGER = "#F28B82"


class PictorApp:
    """Provide a desktop interface for local and API image generation."""

    def __init__(self, root: tk.Tk, settings: Settings):
        self.root = root
        self.settings = settings
        self.client: PictorClient | LocalImageProvider | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.current_preview: Path | None = None
        self.history_paths: dict[str, Path] = {}
        self.generation_busy = False

        self._configure_window()
        self._build_layout()
        self._show_page("create")
        loading_text = (
            "Загружаю модель — первый запуск может быть долгим…"
            if settings.provider == "local"
            else "Проверяю настройки…"
        )
        self._set_status(loading_text, MUTED)
        threading.Thread(target=self._initialize_client, daemon=True).start()

    def _configure_window(self) -> None:
        self.root.title("Pictor — ваша идея, ваша картина")
        self.root.geometry("1120x760")
        self.root.minsize(940, 650)
        self.root.configure(bg=BACKGROUND)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Pictor.TCombobox",
            fieldbackground=SURFACE_LIGHT,
            background=SURFACE_LIGHT,
            foreground=TEXT,
            arrowcolor=ACCENT,
            bordercolor=SURFACE_LIGHT,
            lightcolor=SURFACE_LIGHT,
            darkcolor=SURFACE_LIGHT,
            padding=10,
        )
        style.map(
            "Pictor.TCombobox",
            fieldbackground=[("readonly", SURFACE_LIGHT)],
            foreground=[("readonly", TEXT)],
        )
        style.configure(
            "Pictor.Treeview",
            background=SURFACE,
            fieldbackground=SURFACE,
            foreground=TEXT,
            rowheight=36,
            borderwidth=0,
        )
        style.configure(
            "Pictor.Treeview.Heading",
            background=SURFACE_LIGHT,
            foreground=MUTED,
            relief="flat",
            padding=9,
        )
        style.map(
            "Pictor.Treeview",
            background=[("selected", "#4A3C68")],
            foreground=[("selected", TEXT)],
        )

    def _build_layout(self) -> None:
        header = tk.Frame(self.root, bg=BACKGROUND, height=76)
        header.pack(fill="x", padx=28, pady=(20, 12))
        header.pack_propagate(False)

        logo = tk.Label(
            header,
            text="✦",
            bg=ACCENT,
            fg=BACKGROUND,
            font=("Segoe UI", 18, "bold"),
            width=3,
            height=1,
        )
        logo.pack(side="left", pady=12)

        brand = tk.Frame(header, bg=BACKGROUND)
        brand.pack(side="left", padx=12)
        tk.Label(
            brand,
            text="PICTOR",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="Твоя идея становится картиной",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.status_label = tk.Label(
            header,
            text="Подключение…",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 9),
            padx=14,
            pady=8,
        )
        self.status_label.pack(side="right", pady=16)

        body = tk.Frame(self.root, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        sidebar = tk.Frame(body, bg=SIDEBAR, width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(
            sidebar,
            text="ТВОРЧЕСКАЯ СТУДИЯ",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=18, pady=(22, 12))

        self.create_nav = self._nav_button(
            sidebar, "✧   Новая картина", lambda: self._show_page("create")
        )
        self.create_nav.pack(fill="x", padx=10, pady=3)
        self.history_nav = self._nav_button(
            sidebar, "▧   Моя галерея", lambda: self._show_page("history")
        )
        self.history_nav.pack(fill="x", padx=10, pady=3)

        tk.Frame(sidebar, bg=SURFACE_LIGHT, height=1).pack(
            fill="x", padx=18, pady=18
        )
        tk.Label(
            sidebar,
            text="Pictor создаёт картинки\nпо твоему описанию.\n\n"
            "Генерация работает\nна твоём компьютере.",
            bg=SIDEBAR,
            fg=MUTED,
            justify="left",
            font=("Segoe UI", 9),
            wraplength=155,
        ).pack(anchor="w", padx=18)

        self.pages = tk.Frame(body, bg=BACKGROUND)
        self.pages.pack(side="left", fill="both", expand=True, padx=(24, 0))
        self.create_page = tk.Frame(self.pages, bg=BACKGROUND)
        self.history_page = tk.Frame(self.pages, bg=BACKGROUND)
        self._build_create_page()
        self._build_history_page()

    @staticmethod
    def _nav_button(
        parent: tk.Widget, text: str, command: Callable[[], None]
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            anchor="w",
            bg=SIDEBAR,
            fg=MUTED,
            activebackground=SURFACE_LIGHT,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=11,
            font=("Segoe UI", 10),
            cursor="hand2",
        )

    def _build_create_page(self) -> None:
        tk.Label(
            self.create_page,
            text="Придумай. Опиши. Создай.",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", pady=(8, 3))
        tk.Label(
            self.create_page,
            text="Расскажи, что хочешь увидеть — Pictor нарисует это для тебя.",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 18))

        columns = tk.Frame(self.create_page, bg=BACKGROUND)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=5, uniform="content")
        columns.columnconfigure(1, weight=6, uniform="content")
        columns.rowconfigure(0, weight=1)

        controls = tk.Frame(columns, bg=SURFACE, padx=20, pady=18)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        preview = tk.Frame(columns, bg=SURFACE, padx=18, pady=18)
        preview.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(
            controls,
            text="ТВОЯ ИДЕЯ",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            controls,
            text="Что нарисовать?",
            bg=SURFACE,
            fg=TEXT,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(8, 9))

        self.prompt_text = tk.Text(
            controls,
            height=5,
            wrap="word",
            bg=SURFACE_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#4A3C68",
            relief="flat",
            padx=12,
            pady=11,
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground=SURFACE_LIGHT,
            highlightcolor=ACCENT,
        )
        self.prompt_text.pack(fill="x")
        self.prompt_text.bind("<KeyRelease>", lambda _event: self._update_prompt())
        tk.Label(
            controls,
            text="Например: красная машина на горной дороге",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            controls,
            text="ХУДОЖЕСТВЕННЫЙ СТИЛЬ",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(18, 8))
        self.style_var = tk.StringVar(value=next(iter(ART_STYLES.values()))[0])
        self.style_box = ttk.Combobox(
            controls,
            textvariable=self.style_var,
            values=[label for label, _ in ART_STYLES.values()] + ["Свой стиль"],
            state="readonly",
            style="Pictor.TCombobox",
        )
        self.style_box.pack(fill="x")
        self.style_box.bind("<<ComboboxSelected>>", self._on_style_changed)
        self.custom_style = tk.Entry(
            controls,
            bg=SURFACE_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.custom_style.bind("<KeyRelease>", lambda _event: self._update_prompt())

        self.prompt_preview = tk.Label(
            controls,
            text="Здесь появится промт для модели",
            bg=SURFACE,
            fg=MUTED,
            justify="left",
            anchor="nw",
            wraplength=360,
            font=("Segoe UI", 9),
        )
        self.prompt_preview.pack(fill="x", pady=(14, 14))

        self.generate_button = tk.Button(
            controls,
            text="✦   Создать картину",
            command=self._generate,
            bg=ACCENT,
            fg=BACKGROUND,
            activebackground=ACCENT_HOVER,
            activeforeground=BACKGROUND,
            disabledforeground="#5D5868",
            relief="flat",
            borderwidth=0,
            pady=12,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            state="disabled",
        )
        self.generate_button.pack(fill="x", side="bottom")

        preview_header = tk.Frame(preview, bg=SURFACE)
        preview_header.pack(fill="x", pady=(0, 12))
        tk.Label(
            preview_header,
            text="ХОЛСТ",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        self.preview_path_label = tk.Label(
            preview_header,
            text="Твоя картина появится здесь",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 8),
        )
        self.preview_path_label.pack(side="right")

        self.preview_canvas = tk.Label(
            preview,
            text="✧\n\nОпиши свою идею\nи нажми «Создать картину»",
            bg="#171A24",
            fg="#858DA1",
            justify="center",
            font=("Segoe UI", 13),
        )
        self.preview_canvas.pack(fill="both", expand=True)

    def _build_history_page(self) -> None:
        tk.Label(
            self.history_page,
            text="Моя галерея",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", pady=(8, 3))
        tk.Label(
            self.history_page,
            text="Все картины, созданные в Pictor.",
            bg=BACKGROUND,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 18))

        gallery = tk.Frame(self.history_page, bg=SURFACE, padx=14, pady=14)
        gallery.pack(fill="both", expand=True)
        self.history_tree = ttk.Treeview(
            gallery,
            columns=("date", "size", "name"),
            show="headings",
            style="Pictor.Treeview",
        )
        self.history_tree.heading("date", text="Создано")
        self.history_tree.heading("size", text="Размер")
        self.history_tree.heading("name", text="Файл")
        self.history_tree.column("date", width=145, stretch=False)
        self.history_tree.column("size", width=90, stretch=False)
        self.history_tree.column("name", width=300)
        self.history_tree.pack(fill="both", expand=True)
        self.history_tree.bind("<Double-1>", self._open_selected_history)

        bottom = tk.Frame(gallery, bg=SURFACE)
        bottom.pack(fill="x", pady=(12, 0))
        self.history_count = tk.Label(
            bottom, text="", bg=SURFACE, fg=MUTED, font=("Segoe UI", 9)
        )
        self.history_count.pack(side="left")
        tk.Button(
            bottom,
            text="Показать картину",
            command=self._open_selected_history,
            bg=SURFACE_LIGHT,
            fg=TEXT,
            activebackground="#343B4E",
            activeforeground=TEXT,
            relief="flat",
            padx=12,
            pady=8,
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="right")

    def _show_page(self, page: str) -> None:
        self.create_page.pack_forget()
        self.history_page.pack_forget()
        if page == "history":
            self._refresh_history()
            self.history_page.pack(fill="both", expand=True)
        else:
            self.create_page.pack(fill="both", expand=True)

        self.create_nav.configure(
            bg=SURFACE if page == "create" else SIDEBAR,
            fg=TEXT if page == "create" else MUTED,
        )
        self.history_nav.configure(
            bg=SURFACE if page == "history" else SIDEBAR,
            fg=TEXT if page == "history" else MUTED,
        )

    def _on_style_changed(self, _event=None) -> None:
        if self.style_var.get() == "Свой стиль":
            self.custom_style.pack(fill="x", pady=(8, 0), before=self.prompt_preview)
        else:
            self.custom_style.pack_forget()
        self._update_prompt()

    def _selected_style(self) -> str:
        selected = self.style_var.get()
        if selected == "Свой стиль":
            return self.custom_style.get().strip()
        for label, prompt in ART_STYLES.values():
            if selected == label:
                return prompt
        return ""

    def _update_prompt(self) -> None:
        subject = self.prompt_text.get("1.0", "end").strip()
        style = self._selected_style()
        if not subject or not style:
            self.prompt_preview.configure(
                text="Добавь описание и выбери стиль — здесь появится промт для модели.",
                fg=MUTED,
            )
            return
        prompt = build_generation_prompt(subject, style)
        self.prompt_preview.configure(text=prompt, fg="#C6CBD6")

    def _set_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text, fg=color)

    def _initialize_client(self) -> None:
        try:
            self.settings.output_dir.mkdir(parents=True, exist_ok=True)
            if self.settings.provider == "local":
                client = LocalImageProvider(
                    self.settings.local_model,
                    self.settings.output_dir,
                    self.settings.local_device,
                )
            elif self.settings.provider == "openai":
                client = PictorClient(self.settings)
            else:
                raise PictorAPIError(
                    "Неизвестный PICTOR_PROVIDER. Укажите local или openai в .env."
                )
        except Exception as exc:
            if isinstance(exc, PictorAPIError):
                message = str(exc)
            else:
                message = (
                    "Не удалось запустить модель. Проверьте установку зависимостей "
                    "и свободное место на диске."
                )
            self.root.after(0, self._client_failed, message)
            return
        self.root.after(0, self._client_ready, client)

    def _client_ready(self, client: PictorClient | LocalImageProvider) -> None:
        self.client = client
        provider_name = (
            "Локальная модель готова"
            if self.settings.provider == "local"
            else "Готов к созданию"
        )
        self._set_status(provider_name, SUCCESS)
        self.generate_button.configure(state="normal")
        self._update_prompt()

    def _client_failed(self, message: str) -> None:
        self._set_status("Не удалось подключиться", DANGER)
        self.generate_button.configure(state="disabled")
        messagebox.showerror("Pictor — ошибка запуска", message, parent=self.root)

    def _generate(self) -> None:
        subject = self.prompt_text.get("1.0", "end").strip()
        style = self._selected_style()
        if not subject:
            messagebox.showinfo(
                "Нужно описание",
                "Напиши, что именно нужно нарисовать.",
                parent=self.root,
            )
            self.prompt_text.focus_set()
            return
        if not style:
            messagebox.showinfo(
                "Нужен стиль",
                "Выбери стиль или введи свой.",
                parent=self.root,
            )
            return
        if self.client is None:
            messagebox.showinfo(
                "Модель загружается",
                "Подожди, пока Pictor подготовит модель.",
                parent=self.root,
            )
            return

        prompt = build_generation_prompt(subject, style)
        self.generation_busy = True
        self.generate_button.configure(state="disabled", text="Создаю картину…")
        self._set_status("Рисую…", ACCENT)
        self.preview_canvas.configure(
            image="",
            text="✧\n\nPictor рисует твою картину…\nЭто может занять несколько минут.",
            fg="#C6CBD6",
        )
        threading.Thread(
            target=self._generate_worker,
            args=(self.client, subject, prompt),
            daemon=True,
        ).start()

    def _generate_worker(
        self,
        client: PictorClient | LocalImageProvider,
        subject: str,
        prompt: str,
    ) -> None:
        try:
            response = client.generate(prompt)
            destination = generate_output_path(client.output_dir, subject)
            saved = save_png(response.data, destination)
        except PictorAPIError as exc:
            self.root.after(0, self._generation_failed, str(exc))
            return
        except OSError:
            self.root.after(
                0,
                self._generation_failed,
                "Не удалось сохранить файл. Проверьте место на диске и права папки output.",
            )
            return
        except Exception:
            self.root.after(
                0,
                self._generation_failed,
                "Во время генерации произошла ошибка. Попробуйте ещё раз.",
            )
            return
        self.root.after(0, self._generation_succeeded, saved)

    def _generation_failed(self, message: str) -> None:
        self.generation_busy = False
        self.generate_button.configure(state="normal", text="✦   Создать картину")
        self._set_status("Готов к работе", SUCCESS)
        messagebox.showerror("Не удалось создать картину", message, parent=self.root)

    def _generation_succeeded(self, path: Path) -> None:
        self.generation_busy = False
        self.generate_button.configure(state="normal", text="✦   Создать картину")
        self._set_status("Картина готова", SUCCESS)
        self._show_image(path)
        self._refresh_history()

    def _show_image(self, path: Path) -> None:
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((760, 560), Image.Resampling.LANCZOS)
        except (OSError, tk.TclError):
            self.preview_canvas.configure(
                image="",
                text="Не удалось показать это изображение.",
                fg=DANGER,
            )
            return
        self.current_preview = path
        photo = ImageTk.PhotoImage(image)
        self.photo = photo
        self.preview_canvas.configure(image=photo, text="")
        self.preview_path_label.configure(text=str(path))

    def _refresh_history(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.history_paths.clear()

        records = list_output_files(self.settings.output_dir)
        for index, (path, modified, size) in enumerate(records):
            item_id = str(index)
            self.history_paths[item_id] = path
            self.history_tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    modified.strftime("%Y-%m-%d %H:%M"),
                    f"{size / 1024:.1f} КБ",
                    path.name,
                ),
            )
        count = len(records)
        self.history_count.configure(
            text=f"{count} " + ("картин" if count != 1 else "картина")
        )

    def _open_selected_history(self, _event=None) -> None:
        selected = self.history_tree.selection()
        if not selected:
            return
        path = self.history_paths.get(selected[0])
        if path is not None:
            self._show_page("create")
            self._show_image(path)


def main() -> None:
    """Launch Pictor's desktop application."""

    root = tk.Tk()
    settings = load_settings()
    PictorApp(root, settings)
    root.mainloop()

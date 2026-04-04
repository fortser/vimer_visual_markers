"""
ВИМЕР — Визуальные Маркеры Естественной Речи
Главное окно приложения.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from engine import (
    TextProcessor, CATEGORIES,
    get_markers_by_category, get_default_profile,
)
from engine.registry import MARKER_REGISTRY, get_marker_by_id
from gui.widgets import CategoryFrame, ProfileBar
from utils import (
    read_text_file, write_text_file, load_profile, save_profile,
    list_profiles, get_sample_text, PROFILES_DIR,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_NAME = "ВИМЕР \u2014 Визуальные Маркеры Естественной Речи"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x780")
        self.minsize(1100, 620)

        self.current_profile_name = "default"
        self.category_frames: list[CategoryFrame] = []

        self._build_menu()
        self._build_layout()
        self._load_profile_by_name("default")

    # ─── Верхняя панель ───────────────────
    def _build_menu(self):
        self.menu_frame = ctk.CTkFrame(self, height=40, fg_color=("gray85", "gray18"))
        self.menu_frame.pack(fill="x", side="top")

        ctk.CTkButton(
            self.menu_frame, text="Открыть файл", width=120,
            command=self._open_file, height=30,
        ).pack(side="left", padx=4, pady=5)

        ctk.CTkButton(
            self.menu_frame, text="Сохранить результат", width=150,
            command=self._save_file, height=30,
        ).pack(side="left", padx=4, pady=5)

        ctk.CTkButton(
            self.menu_frame, text="Тестовый текст", width=130,
            command=self._load_sample, height=30,
        ).pack(side="left", padx=4, pady=5)

        # Разделитель
        ctk.CTkLabel(self.menu_frame, text="  |  ",
                      font=ctk.CTkFont(size=14)).pack(side="left", padx=2)

        # Seed
        ctk.CTkLabel(self.menu_frame, text="Seed:",
                      font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 4), pady=5)
        self.seed_var = ctk.StringVar(value="")
        self.seed_entry = ctk.CTkEntry(
            self.menu_frame, textvariable=self.seed_var,
            width=75, height=28, placeholder_text="авто",
        )
        self.seed_entry.pack(side="left", padx=4, pady=5)

        # Разделитель
        ctk.CTkLabel(self.menu_frame, text="  |  ",
                      font=ctk.CTkFont(size=14)).pack(side="left", padx=2)

        # Множитель
        ctk.CTkLabel(self.menu_frame, text="Множитель:",
                      font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 4), pady=5)
        self.mult_var = ctk.DoubleVar(value=1.0)
        self.mult_slider = ctk.CTkSlider(
            self.menu_frame, from_=0, to=3.0, number_of_steps=30,
            variable=self.mult_var, width=130,
        )
        self.mult_slider.pack(side="left", padx=4, pady=5)
        self.mult_label = ctk.CTkLabel(
            self.menu_frame, text="100%",
            font=ctk.CTkFont(size=13, weight="bold"), width=55,
        )
        self.mult_label.pack(side="left", padx=4, pady=5)
        self.mult_var.trace_add("write", self._update_mult_label)

    def _update_mult_label(self, *args):
        pct = int(self.mult_var.get() * 100)
        self.mult_label.configure(text=f"{pct}%")

    # ─── Основной layout ──────────────────
    def _build_layout(self):
        self.main_pane = ctk.CTkFrame(self, fg_color="transparent")
        self.main_pane.pack(fill="both", expand=True, padx=6, pady=6)

        # === ЛЕВАЯ ПАНЕЛЬ (маркеры) — расширена до 540px ===
        self.left_panel = ctk.CTkFrame(self.main_pane, width=540)
        self.left_panel.pack(side="left", fill="y", padx=(0, 6))
        self.left_panel.pack_propagate(False)

        # Профили
        profiles = [p['filename'] for p in list_profiles()]
        if not profiles:
            profiles = ["default"]
        self.profile_bar = ProfileBar(
            self.left_panel,
            on_load_callback=self._load_profile_by_name,
            on_save_callback=self._save_current_profile,
            profiles_list=profiles,
        )
        self.profile_bar.pack(fill="x", padx=4, pady=(4, 8))

        # Кнопки управления категориями
        cat_btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        cat_btn_frame.pack(fill="x", padx=4, pady=(0, 4))

        ctk.CTkButton(
            cat_btn_frame, text="Развернуть все", width=100, height=24,
            font=ctk.CTkFont(size=11),
            command=self._expand_all,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            cat_btn_frame, text="Свернуть все", width=100, height=24,
            font=ctk.CTkFont(size=11),
            command=self._collapse_all,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            cat_btn_frame, text="Сброс на 0", width=90, height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("gray70", "gray35"),
            command=self._reset_all_to_zero,
        ).pack(side="right")

        # Скролл-контейнер для категорий (динамический счётчик)
        total_markers = len(MARKER_REGISTRY)
        self.markers_scroll = ctk.CTkScrollableFrame(
            self.left_panel,
            label_text=f"Маркеры ({total_markers})",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.markers_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        for cat_name in CATEGORIES:
            markers = get_markers_by_category(cat_name)
            if markers:
                cf = CategoryFrame(self.markers_scroll, cat_name, markers)
                cf.pack(fill="x", pady=2)
                self.category_frames.append(cf)

        # === ПРАВАЯ ПАНЕЛЬ (тексты) ===
        self.right_panel = ctk.CTkFrame(self.main_pane)
        self.right_panel.pack(side="right", fill="both", expand=True)

        # Исходный текст
        ctk.CTkLabel(
            self.right_panel, text="Исходный текст:",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(fill="x", padx=8, pady=(8, 2))

        self.input_text = ctk.CTkTextbox(
            self.right_panel,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
        )
        self.input_text.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # Кнопка обработки + статистика
        btn_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=4)

        self.process_btn = ctk.CTkButton(
            btn_frame,
            text="\u26A1  Обработать  (Ctrl+Enter)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._process_text,
        )
        self.process_btn.pack(side="left", padx=(0, 12))

        self.stats_label = ctk.CTkLabel(
            btn_frame, text="",
            font=ctk.CTkFont(size=11), anchor="w",
            wraplength=500,
        )
        self.stats_label.pack(side="left", fill="x", expand=True)

        # Результат
        ctk.CTkLabel(
            self.right_panel, text="Результат:",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(fill="x", padx=8, pady=(8, 2))

        self.output_text = ctk.CTkTextbox(
            self.right_panel,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            state="disabled",
        )
        self.output_text.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # Нижняя панель
        bottom_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.copy_btn = ctk.CTkButton(
            bottom_frame, text="Копировать результат",
            width=170, command=self._copy_result, height=30,
        )
        self.copy_btn.pack(side="left")

        self.version_label = ctk.CTkLabel(
            bottom_frame,
            text="ВИМЕР v1.0",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
        )
        self.version_label.pack(side="right", padx=8)

        # Горячие клавиши
        self.bind("<Control-Return>", lambda e: self._process_text())

    # ─── Действия с категориями ───────────
    def _expand_all(self):
        for cf in self.category_frames:
            cf.expand()

    def _collapse_all(self):
        for cf in self.category_frames:
            cf.collapse()

    def _reset_all_to_zero(self):
        for cf in self.category_frames:
            for mid, row in cf.marker_rows.items():
                row.set_value(0)

    # ─── Действия с файлами ───────────────
    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Открыть текстовый файл",
            filetypes=[
                ("Текстовые файлы", "*.txt *.md"),
                ("Все файлы", "*.*"),
            ],
        )
        if path:
            try:
                text = read_text_file(path)
                self.input_text.delete("1.0", "end")
                self.input_text.insert("1.0", text)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _save_file(self):
        path = filedialog.asksaveasfilename(
            title="Сохранить результат",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt *.md"),
                ("Все файлы", "*.*"),
            ],
        )
        if path:
            try:
                text = self.output_text.get("1.0", "end").rstrip('\n')
                write_text_file(path, text)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _load_sample(self):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", get_sample_text())

    def _copy_result(self):
        text = self.output_text.get("1.0", "end").rstrip('\n')
        if text.strip():
            self.clipboard_clear()
            self.clipboard_append(text)
            self.copy_btn.configure(text="Скопировано!")
            self.after(1500, lambda: self.copy_btn.configure(
                text="Копировать результат"))

    # ─── Обработка текста ─────────────────
    def _process_text(self):
        source = self.input_text.get("1.0", "end").rstrip('\n')
        if not source.strip():
            self.stats_label.configure(
                text="\u26A0  Введите текст для обработки")
            return

        # Собираем профиль из виджетов
        profile = {}
        for cf in self.category_frames:
            profile.update(cf.get_values())

        # Seed
        seed = None
        seed_str = self.seed_var.get().strip()
        if seed_str:
            try:
                seed = int(seed_str)
            except ValueError:
                seed = hash(seed_str) % (2 ** 31)

        multiplier = self.mult_var.get()

        processor = TextProcessor(profile, seed=seed, multiplier=multiplier)
        result = processor.process(source)
        stats = processor.get_stats()
        total = processor.get_total_changes()

        # Выводим результат
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self.output_text.configure(state="disabled")

        # Статистика
        active_markers = len(stats)
        if stats:
            details_parts = []
            for mid in sorted(stats.keys()):
                info = get_marker_by_id(mid)
                name = info.name if info else mid
                details_parts.append(f"{mid} {name}: {stats[mid]}")
            details = " | ".join(details_parts)
        else:
            details = "нет изменений"

        self.stats_label.configure(
            text=f"\u2714 Изменений: {total} | "
                 f"Активных маркеров: {active_markers} | {details}")

    # ─── Профили ──────────────────────────
    def _get_current_values(self) -> dict[str, int]:
        values = {}
        for cf in self.category_frames:
            values.update(cf.get_values())
        return values

    def _set_values(self, marker_values: dict[str, int]):
        for cf in self.category_frames:
            cf.set_values(marker_values)

    def _load_profile_by_name(self, name: str):
        path = PROFILES_DIR / f"{name}.json"
        if not path.exists():
            messagebox.showwarning("Профиль", f"Профиль '{name}' не найден")
            return
        try:
            data = load_profile(str(path))
            markers = data.get("markers", {})
            self._reset_all_to_zero()
            self._set_values(markers)
            self.mult_var.set(data.get("multiplier", 1.0))
            self.current_profile_name = name
        except Exception as e:
            messagebox.showerror("Ошибка загрузки профиля", str(e))

    def _save_current_profile(self, name: str, save_as: bool = False):
        if save_as:
            dialog = ctk.CTkInputDialog(
                text="Имя нового профиля:",
                title="Сохранить как...",
            )
            new_name = dialog.get_input()
            if not new_name:
                return
            name = new_name.strip().replace(' ', '_')

        path = PROFILES_DIR / f"{name}.json"

        if path.exists():
            try:
                existing = load_profile(str(path))
                if existing.get("protected", False) and not save_as:
                    messagebox.showwarning(
                        "Защищённый профиль",
                        f"Профиль '{name}' защищён.\n"
                        "Используйте 'Сохранить как...' для копии.",
                    )
                    return
            except Exception:
                pass

        data = {
            "name": name,
            "description": "",
            "version": 1,
            "protected": False,
            "multiplier": self.mult_var.get(),
            "markers": self._get_current_values(),
        }
        try:
            save_profile(str(path), data)
            self.current_profile_name = name
            profiles = [p['filename'] for p in list_profiles()]
            self.profile_bar.update_profiles(profiles)
            self.profile_bar.profile_var.set(name)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

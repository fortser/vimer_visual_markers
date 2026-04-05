"""
Пользовательские виджеты для GUI:
- MarkerRow: строка маркера (checkbox + label + slider + spinbox)
- CategoryFrame: раскрывающаяся секция категории
- ProfileBar: панель управления профилями
"""

import customtkinter as ctk
from engine.registry import MarkerInfo


def _fmt_prob(val: float) -> str:
    """Форматирует вероятность: целые — без точки ("6"), дробные — как есть ("0.5")."""
    if val == int(val):
        return str(int(val))
    return str(round(val, 4)).rstrip('0')


class MarkerRow(ctk.CTkFrame):
    """
    Одна строка маркера:
    [✓] ID Имя          [===slider===] [ 15 % ]
    """

    def __init__(self, master, marker: MarkerInfo, **kwargs):
        super().__init__(master, fg_color="transparent", height=32, **kwargs)
        self.marker = marker
        self._value = ctk.IntVar(value=marker.default_prob)
        self._enabled = ctk.BooleanVar(value=marker.default_prob > 0)
        self._updating = False  # защита от рекурсии

        # ── Колонки ──
        self.grid_columnconfigure(1, weight=1)  # label растягивается
        self.grid_columnconfigure(2, weight=0)  # slider фиксирован
        self.grid_columnconfigure(3, weight=0)  # entry фиксирован
        self.grid_columnconfigure(4, weight=0)  # % label

        # 0: Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self, text="", variable=self._enabled,
            width=20, checkbox_width=18, checkbox_height=18,
            command=self._on_toggle,
        )
        self.checkbox.grid(row=0, column=0, padx=(0, 4), sticky="w")

        # 1: Label (ID + name)
        label_text = f"{marker.id}  {marker.name}"
        self.label = ctk.CTkLabel(
            self, text=label_text, anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.label.grid(row=0, column=1, padx=(0, 8), sticky="w")
        self.label.bind("<Enter>", self._show_tooltip)
        self.label.bind("<Leave>", self._hide_tooltip)

        # 2: Slider (расширен до 150px)
        self.slider = ctk.CTkSlider(
            self, from_=0, to=100, number_of_steps=100,
            variable=self._value, width=150,
            command=self._on_slider_move,
        )
        self.slider.grid(row=0, column=2, padx=(0, 8), sticky="e")

        # 3: Entry (числовое поле)
        self.entry_var = ctk.StringVar(value=str(marker.default_prob))
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.entry_var,
            width=52,
            height=26,
            justify="center",
            font=ctk.CTkFont(size=13, weight="bold"),
            border_width=2,
            corner_radius=4,
        )
        self.entry.grid(row=0, column=3, padx=(0, 2), sticky="e")
        self.entry.bind("<Return>", self._on_entry_submit)
        self.entry.bind("<FocusOut>", self._on_entry_submit)
        self.entry.bind("<Up>", self._on_entry_up)
        self.entry.bind("<Down>", self._on_entry_down)

        # 4: Подпись %
        self.pct_label = ctk.CTkLabel(
            self, text="%", font=ctk.CTkFont(size=11),
            width=16,
        )
        self.pct_label.grid(row=0, column=4, padx=(0, 4), sticky="w")

        # Синхронизация slider -> entry
        self._value.trace_add("write", self._on_var_changed)

        # ── Тултип ──
        self._tooltip = None
        self._tooltip_hide_timer = None
        self._on_toggle()

    def _on_toggle(self):
        enabled = self._enabled.get()
        state = "normal" if enabled else "disabled"
        self.slider.configure(state=state)
        self.entry.configure(state=state)
        if not enabled:
            self._value.set(0)
            self.entry_var.set("0")

    def _on_slider_move(self, value):
        """Slider двигается — обновляем entry."""
        if self._updating:
            return
        self._updating = True
        int_val = int(value)
        self._value.set(int_val)
        self.entry_var.set(str(int_val))
        self._updating = False

    def _on_var_changed(self, *args):
        """IntVar изменился — синхронизируем entry."""
        if self._updating:
            return
        self._updating = True
        try:
            val = self._value.get()
            self.entry_var.set(str(val))
        except Exception:
            pass
        self._updating = False

    def _on_entry_submit(self, event=None):
        """Пользователь ввёл число в entry — синхронизируем slider."""
        if self._updating:
            return
        self._updating = True
        try:
            raw = self.entry_var.get().strip().replace(',', '.')
            val = float(raw) if raw else 0.0
            val = max(0.0, min(100.0, val))
            self._value.set(int(round(val)))  # слайдер — только целые
            self.entry_var.set(_fmt_prob(val))
            if val > 0 and not self._enabled.get():
                self._enabled.set(True)
                self.slider.configure(state="normal")
                self.entry.configure(state="normal")
        except ValueError:
            val = self._value.get()
            self.entry_var.set(_fmt_prob(float(val)))
        self._updating = False

    def _on_entry_up(self, event):
        """Стрелка вверх — +1."""
        try:
            val = min(100.0, float(self.entry_var.get()) + 1)
            self._value.set(int(round(val)))
            self.entry_var.set(_fmt_prob(val))
        except ValueError:
            pass

    def _on_entry_down(self, event):
        """Стрелка вниз — -1."""
        try:
            val = max(0.0, float(self.entry_var.get()) - 1)
            self._value.set(int(round(val)))
            self.entry_var.set(_fmt_prob(val))
        except ValueError:
            pass

    def get_value(self) -> float:
        if not self._enabled.get():
            return 0.0
        try:
            return max(0.0, min(100.0, float(self.entry_var.get())))
        except ValueError:
            return float(self._value.get())

    def set_value(self, val: float):
        val = max(0.0, min(100.0, float(val)))
        self._updating = True
        self._value.set(int(round(val)))  # слайдер — только целые
        self.entry_var.set(_fmt_prob(val))
        self._enabled.set(val > 0)
        self._updating = False
        self._on_toggle()

    # ── Тултип (исправленный) ──────────────

    def _show_tooltip(self, event):
        """Показать тултип с описанием маркера."""
        # Убираем старый, если есть
        self._destroy_tooltip()

        x = event.x_root + 15
        y = event.y_root + 10

        self._tooltip = ctk.CTkToplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        self._tooltip.attributes("-topmost", True)

        # На некоторых системах CTkToplevel показывает анимацию —
        # отключаем через withdraw/deiconify
        self._tooltip.withdraw()

        label = ctk.CTkLabel(
            self._tooltip, text=self.marker.description,
            font=ctk.CTkFont(size=11),
            wraplength=400, justify="left",
            fg_color=("gray90", "gray20"),
            corner_radius=6, padx=10, pady=6,
        )
        label.pack()

        self._tooltip.deiconify()

        # Привязываем скрытие к любому клику внутри тултипа
        self._tooltip.bind("<Button-1>", lambda e: self._destroy_tooltip())

        # Автоскрытие через 3 секунды
        self._tooltip_hide_timer = self.after(3000, self._destroy_tooltip)

        # Привязываем скрытие к скроллу родительского контейнера
        self._bind_scroll_hide()

    def _hide_tooltip(self, event):
        """Скрыть тултип при уходе курсора с label."""
        self._destroy_tooltip()

    def _destroy_tooltip(self):
        """Безопасное уничтожение тултипа."""
        # Отменяем таймер
        if self._tooltip_hide_timer is not None:
            self.after_cancel(self._tooltip_hide_timer)
            self._tooltip_hide_timer = None

        # Убираем привязки скролла
        self._unbind_scroll_hide()

        # Уничтожаем окно
        if self._tooltip is not None:
            try:
                self._tooltip.destroy()
            except Exception:
                pass
            self._tooltip = None

    def _bind_scroll_hide(self):
        """Привязать уничтожение тултипа к событиям скролла.

        Сохраняем funcid каждого binding'а, чтобы при unbind снимать
        только СВОЙ обработчик, не трогая чужие (других MarkerRow).
        """
        self._scroll_canvas = None
        self._scroll_funcids = {}
        self._toplevel_ref = None
        self._toplevel_funcids = {}

        # Ищем ближайший ScrollableFrame вверх по иерархии
        parent = self.master
        while parent is not None:
            if isinstance(parent, ctk.CTkScrollableFrame):
                try:
                    canvas = parent._parent_canvas
                    fids = {}
                    for event in ('<MouseWheel>', '<Button-4>', '<Button-5>', '<Configure>'):
                        fid = canvas.bind(event, self._on_scroll_event, add="+")
                        # fid может быть пустой строкой на некоторых сборках tk
                        if fid:
                            fids[event] = fid
                    self._scroll_canvas = canvas
                    self._scroll_funcids = fids
                except AttributeError:
                    pass
                break
            parent = getattr(parent, 'master', None)

        # Привязываем к перемещению/сворачиванию главного окна
        try:
            toplevel = self.winfo_toplevel()
            tfids = {}
            for event in ('<Configure>', '<Unmap>'):
                fid = toplevel.bind(event, self._on_window_event, add="+")
                if fid:
                    tfids[event] = fid
            self._toplevel_ref = toplevel
            self._toplevel_funcids = tfids
        except Exception:
            pass

    def _unbind_scroll_hide(self):
        """Снять только свои binding'и, не трогая привязки других виджетов."""
        canvas = getattr(self, '_scroll_canvas', None)
        if canvas is not None:
            for event, fid in getattr(self, '_scroll_funcids', {}).items():
                try:
                    canvas.unbind(event, fid)
                except Exception:
                    pass
            self._scroll_canvas = None
            self._scroll_funcids = {}

        toplevel = getattr(self, '_toplevel_ref', None)
        if toplevel is not None:
            for event, fid in getattr(self, '_toplevel_funcids', {}).items():
                try:
                    toplevel.unbind(event, fid)
                except Exception:
                    pass
            self._toplevel_ref = None
            self._toplevel_funcids = {}

    def _on_scroll_event(self, event):
        """При скролле — убираем тултип."""
        self._destroy_tooltip()

    def _on_window_event(self, event):
        """При перемещении/сворачивании окна — убираем тултип."""
        self._destroy_tooltip()


class CategoryFrame(ctk.CTkFrame):
    """Раскрывающаяся категория с маркерами."""

    def __init__(self, master, category_name: str,
                 markers: list[MarkerInfo], **kwargs):
        super().__init__(master, **kwargs)
        self.category_name = category_name
        self._expanded = False
        self.marker_rows: dict[str, MarkerRow] = {}

        # Заголовок — кнопка-аккордеон
        self.header = ctk.CTkButton(
            self,
            text=f"  \u25B6  {category_name}  ({len(markers)})",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35"),
            text_color=("gray10", "gray90"),
            command=self.toggle,
            height=34,
        )
        self.header.pack(fill="x", padx=2, pady=(2, 0))

        # Контейнер маркеров (скрыт по умолчанию)
        self.content = ctk.CTkFrame(self, fg_color="transparent")

        for m in markers:
            row = MarkerRow(self.content, m)
            row.pack(fill="x", padx=(12, 4), pady=2)
            self.marker_rows[m.id] = row

    def toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.content.pack(fill="x", padx=2, pady=(0, 4))
            arrow = "\u25BC"
        else:
            self.content.pack_forget()
            arrow = "\u25B6"
        self.header.configure(
            text=f"  {arrow}  {self.category_name}  ({len(self.marker_rows)})")

    def expand(self):
        if not self._expanded:
            self.toggle()

    def collapse(self):
        if self._expanded:
            self.toggle()

    def get_values(self) -> dict[str, int]:
        return {mid: row.get_value() for mid, row in self.marker_rows.items()}

    def set_values(self, values: dict[str, int]):
        for mid, row in self.marker_rows.items():
            if mid in values:
                row.set_value(values[mid])


class ProfileBar(ctk.CTkFrame):
    """Панель профилей: выбор, загрузка, сохранение (двухстрочная компоновка)."""

    def __init__(self, master, on_load_callback, on_save_callback,
                 profiles_list: list[str], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_load = on_load_callback
        self.on_save = on_save_callback

        # ── Первая строка: выбор профиля ──
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            row1, text="Профиль:", font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 6))

        self.profile_var = ctk.StringVar(
            value=profiles_list[0] if profiles_list else "default")
        self.combo = ctk.CTkComboBox(
            row1, values=profiles_list, variable=self.profile_var,
            width=160, command=self._on_select,
        )
        self.combo.pack(side="left", padx=(0, 6))

        # ── Вторая строка: кнопки управления ──
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x")

        self.btn_load = ctk.CTkButton(
            row2, text="Загрузить", width=85, command=self._do_load, height=28)
        self.btn_load.pack(side="left", padx=(0, 4))

        self.btn_save = ctk.CTkButton(
            row2, text="Сохранить", width=85, command=self._do_save, height=28)
        self.btn_save.pack(side="left", padx=(0, 4))

        self.btn_save_as = ctk.CTkButton(
            row2, text="Сохранить как...", width=120,
            command=self._do_save_as, height=28)
        self.btn_save_as.pack(side="left")

    def _on_select(self, value):
        pass

    def _do_load(self):
        self.on_load(self.profile_var.get())

    def _do_save(self):
        self.on_save(self.profile_var.get(), save_as=False)

    def _do_save_as(self):
        self.on_save(self.profile_var.get(), save_as=True)

    def update_profiles(self, profiles_list: list[str]):
        self.combo.configure(values=profiles_list)

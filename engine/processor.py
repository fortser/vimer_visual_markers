"""
Главный движок обработки текста.
Принимает текст + профиль (словарь {marker_id: probability}),
применяет маркеры в определённом порядке, собирает статистику.

Порядок: структура → лексика → типографика → пунктуация →
         пропущенные пробелы → лишние пробелы → опечатки →
         эмоциональные → регистр
"""

import random
from engine.markers import MARKER_FUNCTIONS

# Порядок применения маркеров
APPLY_ORDER: list[str] = [
    # 7. Структура (сначала — меняют структуру абзацев)
    "7.2", "7.3", "7.4",
    # 8. Лексика
    "8.7", "8.8",
    # 5. Кавычки, тире, типографика
    "5.7",  # ё→е первым (меняет буквы, не структуру)
    "5.1", "5.2",  # кавычки
    "5.3", "5.4", "5.5",  # тире → замены
    "5.6",  # дефис в составных словах
    "5.8", "5.9",  # пропуск закрывающих
    # 4. Пунктуация (после структуры, до пробелов)
    "4.9", "4.10", "4.12",  # Сначала добавление/удаление запятых
    "4.1", "4.2", "4.3", "4.4",  # Дублирование знаков
    "4.5", "4.6", "4.7",  # Многоточия
    "4.11", "4.8",  # Двойная точка, пропуск точки
    # 3. Пропущенные пробелы
    "3.1", "3.2", "3.3", "3.4",
    # 2. Лишние пробелы
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9",
    # 6. Опечатки набора (после пробелов)
    "6.1", "6.2", "6.3", "6.4", "6.5",
    # 10. Эмоциональные (после опечаток, до регистра)
    "10.1", "10.4",
    # 1. Регистр и капитализация (в самом конце)
    "1.1", "1.2", "1.3", "1.4", "1.6",
]


class TextProcessor:
    def __init__(self, profile: dict[str, int], seed: int | None = None,
                 multiplier: float = 1.0):
        """
        profile: {marker_id: probability 0-100}
        seed: для воспроизводимости
        multiplier: глобальный множитель 0.0 - 3.0
        """
        self.profile = profile
        self.seed = seed
        self.multiplier = multiplier
        self.stats: dict[str, int] = {}

    def _effective_prob(self, marker_id: str) -> int:
        """Получить эффективную вероятность с учётом множителя."""
        base = self.profile.get(marker_id, 0)
        return min(100, max(0, int(base * self.multiplier)))

    def process(self, text: str) -> str:
        """Применяет все активные маркеры и возвращает модифицированный текст."""
        if self.seed is not None:
            random.seed(self.seed)

        self.stats = {}
        result = text

        for marker_id in APPLY_ORDER:
            prob = self._effective_prob(marker_id)
            if prob <= 0:
                continue

            func = MARKER_FUNCTIONS.get(marker_id)
            if func is None:
                continue

            result, count = func(result, prob)
            if count > 0:
                self.stats[marker_id] = count

        return result

    def get_stats(self) -> dict[str, int]:
        """Возвращает статистику {marker_id: количество применений}."""
        return dict(self.stats)

    def get_total_changes(self) -> int:
        return sum(self.stats.values())

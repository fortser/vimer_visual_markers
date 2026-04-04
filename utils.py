"""
Утилиты: чтение/запись файлов, определение кодировки.
"""

import json
import os
from pathlib import Path

PROFILES_DIR = Path(__file__).parent / "profiles"
DATA_DIR = Path(__file__).parent / "data"
SAMPLE_TEXT_PATH = DATA_DIR / "sample_text.txt"


def read_text_file(path: str) -> str:
    """Читает текстовый файл с автоопределением кодировки."""
    for encoding in ('utf-8', 'utf-8-sig', 'cp1251', 'latin-1'):
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"Не удалось определить кодировку файла: {path}")


def write_text_file(path: str, text: str, encoding: str = 'utf-8') -> None:
    with open(path, 'w', encoding=encoding) as f:
        f.write(text)


def load_profile(path: str) -> dict:
    """Загружает JSON-профиль."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_profile(path: str, data: dict) -> None:
    """Сохраняет JSON-профиль."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_profiles() -> list[dict]:
    """Возвращает список профилей из папки profiles/."""
    profiles = []
    if PROFILES_DIR.exists():
        for p in sorted(PROFILES_DIR.glob('*.json')):
            try:
                data = load_profile(str(p))
                profiles.append({
                    'path': str(p),
                    'filename': p.stem,
                    'name': data.get('name', p.stem),
                    'description': data.get('description', ''),
                    'protected': data.get('protected', False),
                })
            except Exception:
                continue
    return profiles


def get_sample_text() -> str:
    """Возвращает встроенный тестовый текст."""
    if SAMPLE_TEXT_PATH.exists():
        return read_text_file(str(SAMPLE_TEXT_PATH))
    return _DEFAULT_SAMPLE_TEXT


_DEFAULT_SAMPLE_TEXT = """Вчера я ходил в магазин и купил несколько продуктов. Погода была хорошая, поэтому решил пройтись пешком. По дороге встретил старого знакомого — мы не виделись около пяти лет.

Он рассказал, что переехал в другой город и работает в крупной компании. «Всё отлично», — сказал он. Мы обменялись номерами телефонов и договорились встретиться на следующей неделе.

Когда я вернулся домой, обнаружил, что забыл купить хлеб. Это было немного досадно, но я решил не расстраиваться. В конце концов, можно заказать доставку или сходить в ближайший магазин завтра утром.

Вечером мы с семьёй смотрели новый фильм. Фильм оказался интересным, хотя начало было немного затянутым. Дети были в восторге! Они сказали, что хотят посмотреть продолжение. Мне тоже понравилось, особенно финальная сцена.

Перед сном я прочитал пару глав книги. Автор пишет очень увлекательно — невозможно оторваться. Рекомендую всем, кто любит детективы и загадки."""

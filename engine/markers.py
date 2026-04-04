"""
Реализация 51 маркера по спецификации 8.5.
Каждая функция принимает текст и вероятность,
возвращает (модифицированный текст, количество применений).

Нумерация строго соответствует спецификации:
  1.1-1.4, 1.6
  2.1-2.9
  3.1-3.4
  4.1-4.12
  5.1-5.9
  6.1-6.5
  7.2-7.4
  8.7-8.8
  10.1, 10.4
"""

import random
import re
from engine.keyboard_map import get_adjacent_key


# ─── Утилиты ────────────────────────────────────────

def _coin(prob: int) -> bool:
    """Бросок монетки с вероятностью prob (0-100)."""
    return random.randint(1, 100) <= prob


def _sentences(text: str) -> list[str]:
    """Грубое разбиение на предложения по [.!?]+"""
    parts = re.split(r'(?<=[.!?\u2026])\s+', text)
    return [p for p in parts if p.strip()]


# ═══════════════════════════════════════════════════
# 1. РЕГИСТР И КАПИТАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════

def marker_1_1(text: str, prob: int) -> tuple[str, int]:
    """Строчная буква в начале предложения (после . ! ?)."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' ' + m.group(2).lower()
        return m.group(0)

    result = re.sub(r'([.!?])\s+([А-ЯЁ])', repl, text)
    return result, count


def marker_1_2(text: str, prob: int) -> tuple[str, int]:
    """Строчная буква в начале абзаца."""
    count = 0
    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped and re.match(r'[А-ЯЁ]', stripped[0]):
            if _coin(prob):
                indent = line[:len(line) - len(stripped)]
                lines[i] = indent + stripped[0].lower() + stripped[1:]
                count += 1
    return '\n'.join(lines), count


def marker_1_3(text: str, prob: int) -> tuple[str, int]:
    """Две заглавные буквы в начале слова (слово ≥ 3 букв): ПОтом, НАверное."""
    count = 0

    def repl(m):
        nonlocal count
        word = m.group(0)
        if len(word) >= 3 and _coin(prob):
            count += 1
            return word[0].upper() + word[1].upper() + word[2:]
        return word

    result = re.sub(r'(?<=[\.\!\?\n] )[А-ЯЁ][а-яё]{2,}', repl, text)
    if text and text[0].isupper() and len(text) >= 3 and _coin(prob):
        result = result[0].upper() + result[1].upper() + result[2:]
        count += 1
    return result, count


def marker_1_4(text: str, prob: int) -> tuple[str, int]:
    """Случайная заглавная в середине предложения."""
    count = 0
    words = text.split(' ')
    for i in range(1, len(words)):
        w = words[i]
        if w and re.match(r'[а-яё]', w[0]) and len(w) >= 3:
            if _coin(prob):
                words[i] = w[0].upper() + w[1:]
                count += 1
    return ' '.join(words), count


def marker_1_6(text: str, prob: int) -> tuple[str, int]:
    """Строчное «я».

    Заменяет местоимение Я на я в любой позиции:
    в начале текста/строки, в середине и в конце.
    (?<!\S) = позиция начала строки или после пробела/\n.
    (?!\S)  = позиция конца строки или перед пробелом/\n.
    """
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return 'я'
        return m.group(0)

    result = re.sub(r'(?<!\S)Я(?!\S)', repl, text)
    return result, count


# ═══════════════════════════════════════════════════
# 2. ЛИШНИЕ ПРОБЕЛЫ
# ═══════════════════════════════════════════════════

def _insert_space_before(text: str, char: str, prob: int) -> tuple[str, int]:
    """Вставляет пробел перед символом char."""
    count = 0
    escaped = re.escape(char)

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' ' + char
        return m.group(0)

    result = re.sub(r'(\S)' + escaped, repl, text)
    return result, count


def marker_2_1(text: str, prob: int) -> tuple[str, int]:
    """Пробел перед запятой."""
    return _insert_space_before(text, ',', prob)


def marker_2_2(text: str, prob: int) -> tuple[str, int]:
    """Пробел перед точкой (не многоточием, не в числах, не в аббревиатурах).

    Срабатывает только если точка завершает кириллическое слово или ')':
      - исключает десятичные числа: 3.14, 2.0
      - исключает расширения файлов и домены: test.txt, v1.2
      - исключает аббревиатуры типа т.е., т.д. (после точки — буква вплотную)
    """
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' .'
        return m.group(0)

    # Перед точкой должно быть слово ≥ 3 кириллических букв или ')'.
    # Это отсекает однобуквенные аббревиатуры (т., е., д.) и двухбуквенные (не., он.)
    # (?!\.) — не многоточие
    # (?![0-9a-zA-Zа-яёА-ЯЁ]) — после точки не идёт буква/цифра вплотную
    result = re.sub(r'([а-яёА-ЯЁ]{3,}|\))\.(?!\.)(?![0-9a-zA-Zа-яёА-ЯЁ])', repl, text)
    return result, count


def marker_2_3(text: str, prob: int) -> tuple[str, int]:
    """Пробел перед ?/!"""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' ' + m.group(2)
        return m.group(0)

    result = re.sub(r'(\S)([!?])', repl, text)
    return result, count


def marker_2_4(text: str, prob: int) -> tuple[str, int]:
    """Пробел перед :/; (объединённый маркер)."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' ' + m.group(2)
        return m.group(0)

    result = re.sub(r'(\S)([:;])', repl, text)
    return result, count


def marker_2_5(text: str, prob: int) -> tuple[str, int]:
    """Двойной пробел между словами."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + '  ' + m.group(2)
        return m.group(0)

    result = re.sub(r'(\S) (\S)', repl, text)
    return result, count


def marker_2_6(text: str, prob: int) -> tuple[str, int]:
    """Пробел после открывающей скобки."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '( ' + m.group(1)
        return m.group(0)

    result = re.sub(r'\((\S)', repl, text)
    return result, count


def marker_2_7(text: str, prob: int) -> tuple[str, int]:
    """Пробел перед закрывающей скобкой."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' )'
        return m.group(0)

    result = re.sub(r'(\S)\)', repl, text)
    return result, count


def marker_2_8(text: str, prob: int) -> tuple[str, int]:
    """Пробел после открывающей кавычки «."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '\u00AB ' + m.group(1)
        return m.group(0)

    result = re.sub(r'\u00AB(\S)', repl, text)
    return result, count


def marker_2_9(text: str, prob: int) -> tuple[str, int]:
    """Пробел перед закрывающей кавычкой »."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' \u00BB'
        return m.group(0)

    result = re.sub(r'(\S)\u00BB', repl, text)
    return result, count


# ═══════════════════════════════════════════════════
# 3. ПРОПУЩЕННЫЕ ПРОБЕЛЫ
# ═══════════════════════════════════════════════════

def marker_3_1(text: str, prob: int) -> tuple[str, int]:
    """Удаляет пробел после запятой."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return ','
        return m.group(0)

    result = re.sub(r', (?=\S)', repl, text)
    return result, count


def marker_3_2(text: str, prob: int) -> tuple[str, int]:
    """Удаляет пробел после точки."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '.'
        return m.group(0)

    result = re.sub(r'\. (?=[А-ЯЁа-яё])', repl, text)
    return result, count


def marker_3_3(text: str, prob: int) -> tuple[str, int]:
    """Удаляет пробел после ?/!"""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1)
        return m.group(0)

    result = re.sub(r'([?!]) (?=[А-ЯЁа-яё])', repl, text)
    return result, count


def marker_3_4(text: str, prob: int) -> tuple[str, int]:
    """Слипание тире с соседними словами."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            variant = random.choice(['left', 'right', 'both'])
            if variant == 'left':
                return m.group(1) + '\u2014 ' + m.group(2)
            elif variant == 'right':
                return m.group(1) + ' \u2014' + m.group(2)
            else:
                return m.group(1) + '\u2014' + m.group(2)
        return m.group(0)

    result = re.sub(r'(\S) \u2014 (\S)', repl, text)
    return result, count


# ═══════════════════════════════════════════════════
# 4. ПУНКТУАЦИЯ
# ═══════════════════════════════════════════════════

def marker_4_1(text: str, prob: int) -> tuple[str, int]:
    """Одиночный ! → !! (только одиночные, не затрагивает уже удвоенные)."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '!!'
        return m.group(0)

    # (?<!!) — не предшествует !, (?!!) — не следует !
    # Таким образом захватываем только одиночные !
    result = re.sub(r'(?<!!)!(?!!)', repl, text)
    return result, count


def marker_4_2(text: str, prob: int) -> tuple[str, int]:
    """!! → !!! (только двойные, не одиночные).

    Цепочка при включённых 4.1 + 4.2:
      !  --[4.1]-->  !!  --[4.2]-->  !!!
    Максимальный результат — три восклицания, не четыре.
    """
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '!!!'
        return m.group(0)

    # (?<!!) — не предшествует !, (?!!) — не следует !
    # Захватываем ровно !! (не одиночные, не тройные и длиннее)
    result = re.sub(r'(?<!!)!!(?!!)', repl, text)
    return result, count


def marker_4_3(text: str, prob: int) -> tuple[str, int]:
    """Одиночный ? → ?? (только одиночные, не затрагивает уже удвоенные)."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '??'
        return m.group(0)

    # (?<!\?) — не предшествует ?, (?!\?) — не следует ?
    result = re.sub(r'(?<!\?)\?(?!\?)', repl, text)
    return result, count


def marker_4_4(text: str, prob: int) -> tuple[str, int]:
    """? → ?! (только одиночные ?, не те что уже ?? или ?!)."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '?!'
        return m.group(0)

    # (?<!\?) — не предшествует ?, (?![!?]) — не следует ! или ?
    result = re.sub(r'(?<!\?)\?(?![!?])', repl, text)
    return result, count


def marker_4_5(text: str, prob: int) -> tuple[str, int]:
    """Многоточие вместо точки: . → ..."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '...'
        return m.group(0)

    result = re.sub(r'\.(?=\s|$)(?!\.)', repl, text)
    return result, count


def marker_4_6(text: str, prob: int) -> tuple[str, int]:
    """Многоточие → две точки."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '..'
        return m.group(0)

    result = re.sub(r'\u2026|\.{3}', repl, text)
    return result, count


def marker_4_7(text: str, prob: int) -> tuple[str, int]:
    """Многоточие → 4-5 точек."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '.' * random.randint(4, 5)
        return m.group(0)

    result = re.sub(r'\u2026|\.{3}', repl, text)
    return result, count


def marker_4_8(text: str, prob: int) -> tuple[str, int]:
    """Пропуск точки в конце абзаца."""
    count = 0
    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.endswith('.') and not stripped.endswith('..') and _coin(prob):
            lines[i] = stripped[:-1]
            count += 1
    return '\n'.join(lines), count


def marker_4_9(text: str, prob: int) -> tuple[str, int]:
    """Пропуск запятой перед но/а/что/который."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return ' ' + m.group(1)
        return m.group(0)

    result = re.sub(r', (но|а|что|который|которая|которое|которые)(?=\s)', repl, text)
    return result, count


def marker_4_10(text: str, prob: int) -> tuple[str, int]:
    """Лишняя запятая после ну/вот/так."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + m.group(2) + ', '
        return m.group(0)

    result = re.sub(
        r'((?:^|(?<=\s)))([Нн]у|[Вв]от|[Тт]ак) (?!,)',
        repl, text,
    )
    return result, count


def marker_4_11(text: str, prob: int) -> tuple[str, int]:
    """Двойная точка."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '..'
        return m.group(0)

    result = re.sub(r'\.(?=\s[А-ЯЁ])(?!\.)', repl, text)
    return result, count


def marker_4_12(text: str, prob: int) -> tuple[str, int]:
    """Оксфордская запятая перед и."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ', и ' + m.group(2)
        return m.group(0)

    result = re.sub(r'(\S,\s\S+)\s+и\s+(\S)', repl, text)
    return result, count


# ═══════════════════════════════════════════════════
# 5. КАВЫЧКИ, ТИРЕ, ТИПОГРАФИКА
# ═══════════════════════════════════════════════════

def marker_5_1(text: str, prob: int) -> tuple[str, int]:
    """Ёлочки → лапки."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '\u201E' + m.group(1) + '\u201C'
        return m.group(0)

    result = re.sub(r'\u00AB(.+?)\u00BB', repl, text)
    return result, count


def marker_5_2(text: str, prob: int) -> tuple[str, int]:
    """Ёлочки → прямые кавычки."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '"' + m.group(1) + '"'
        return m.group(0)

    result = re.sub(r'\u00AB(.+?)\u00BB', repl, text)
    return result, count


def marker_5_3(text: str, prob: int) -> tuple[str, int]:
    """Длинное тире → дефис."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '-'
        return m.group(0)

    result = re.sub(r'\u2014', repl, text)
    return result, count


def marker_5_4(text: str, prob: int) -> tuple[str, int]:
    """Длинное тире → короткое."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return '\u2013'
        return m.group(0)

    result = re.sub(r'\u2014', repl, text)
    return result, count


def marker_5_5(text: str, prob: int) -> tuple[str, int]:
    """Длинное тире → дефис с пробелами: ' - '."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' - ' + m.group(2)
        return m.group(0)

    result = re.sub(r'(\S) \u2014 (\S)', repl, text)
    return result, count


def marker_5_6(text: str, prob: int) -> tuple[str, int]:
    """Тире/пробелы вместо дефиса в составных словах: кто-то → кто - то."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + ' - ' + m.group(2)
        return m.group(0)

    result = re.sub(r'([а-яёА-ЯЁ]+)-([а-яёА-ЯЁ]+)', repl, text)
    return result, count


def marker_5_7(text: str, prob: int) -> tuple[str, int]:
    """ё → е."""
    count = 0
    result = []
    for ch in text:
        if ch == '\u0451' and _coin(prob):
            result.append('\u0435')
            count += 1
        elif ch == '\u0401' and _coin(prob):
            result.append('\u0415')
            count += 1
        else:
            result.append(ch)
    return ''.join(result), count


def marker_5_8(text: str, prob: int) -> tuple[str, int]:
    """Пропуск закрывающей скобки (макс 1 раз, при ≥3 парах)."""
    pairs = re.findall(r'\([^)]+\)', text)
    if len(pairs) < 3:
        return text, 0

    count = 0

    def repl(m):
        nonlocal count
        if count == 0 and _coin(prob):
            count += 1
            return '(' + m.group(1)
        return m.group(0)

    result = re.sub(r'\(([^)]+)\)', repl, text)
    return result, count


def marker_5_9(text: str, prob: int) -> tuple[str, int]:
    """Пропуск закрывающей кавычки (макс 1 раз, при ≥3 парах)."""
    pairs = re.findall(r'\u00AB.+?\u00BB', text)
    if len(pairs) < 3:
        return text, 0

    count = 0

    def repl(m):
        nonlocal count
        if count == 0 and _coin(prob):
            count += 1
            return '\u00AB' + m.group(1)
        return m.group(0)

    result = re.sub(r'\u00AB(.+?)\u00BB', repl, text)
    return result, count


# ═══════════════════════════════════════════════════
# 6. ОПЕЧАТКИ НАБОРА
# ═══════════════════════════════════════════════════

def marker_6_1(text: str, prob: int) -> tuple[str, int]:
    """Пропуск буквы в слове ≥ 6 букв, позиция 2..n-2, макс 1/абзац."""
    count = 0
    paragraphs = text.split('\n\n')
    result_paragraphs = []

    for para in paragraphs:
        para_changed = False

        def repl(m):
            nonlocal count, para_changed
            word = m.group(0)
            if not para_changed and len(word) >= 6 and _coin(prob):
                pos = random.randint(2, len(word) - 3)
                count += 1
                para_changed = True
                return word[:pos] + word[pos + 1:]
            return word

        result_paragraphs.append(re.sub(r'[а-яёА-ЯЁ]{6,}', repl, para))

    return '\n\n'.join(result_paragraphs), count


def marker_6_2(text: str, prob: int) -> tuple[str, int]:
    """Перестановка двух соседних букв в слове ≥ 6 букв, позиция 2..n-2."""
    count = 0

    def repl(m):
        nonlocal count
        word = m.group(0)
        if len(word) >= 6 and _coin(prob):
            pos = random.randint(2, len(word) - 3)
            lst = list(word)
            lst[pos], lst[pos + 1] = lst[pos + 1], lst[pos]
            count += 1
            return ''.join(lst)
        return word

    result = re.sub(r'[а-яёА-ЯЁ]{6,}', repl, text)
    return result, count


def marker_6_3(text: str, prob: int) -> tuple[str, int]:
    """Замена на соседнюю клавишу ЙЦУКЕН (слово ≥ 5 букв, позиция 2..n-2)."""
    count = 0

    def repl(m):
        nonlocal count
        word = m.group(0)
        if len(word) >= 5 and _coin(prob):
            pos = random.randint(2, len(word) - 3)
            adj = get_adjacent_key(word[pos])
            if adj:
                count += 1
                return word[:pos] + adj + word[pos + 1:]
        return word

    result = re.sub(r'[а-яёА-ЯЁ]{5,}', repl, text)
    return result, count


def marker_6_4(text: str, prob: int) -> tuple[str, int]:
    """Удвоение буквы в слове ≥ 5 букв."""
    count = 0

    def repl(m):
        nonlocal count
        word = m.group(0)
        if len(word) >= 5 and _coin(prob):
            pos = random.randint(1, len(word) - 2)
            count += 1
            return word[:pos] + word[pos] + word[pos:]
        return word

    result = re.sub(r'[а-яёА-ЯЁ]{5,}', repl, text)
    return result, count


def marker_6_5(text: str, prob: int) -> tuple[str, int]:
    """Удвоение слова из whitelist: очень, давно, нет, да, ну, так, вот, уже, ещё."""
    count = 0
    whitelist = ['очень', 'давно', 'нет', 'да', 'ну', 'так', 'вот', 'уже', 'ещё']
    pattern_str = '|'.join(whitelist)

    def repl(m):
        nonlocal count
        word = m.group(2)
        if word.lower() in whitelist and _coin(prob):
            count += 1
            return m.group(1) + word + ' ' + word + m.group(3)
        return m.group(0)

    result = re.sub(
        r'(\s)(' + pattern_str + r')(\s)',
        repl, text, flags=re.IGNORECASE,
    )
    return result, count


# ═══════════════════════════════════════════════════
# 7. СТРУКТУРА
# ═══════════════════════════════════════════════════

def marker_7_2(text: str, prob: int) -> tuple[str, int]:
    """Слияние коротких абзацев."""
    count = 0
    paragraphs = text.split('\n\n')
    result = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        sents = _sentences(p)
        if (i + 1 < len(paragraphs)
                and len(sents) <= 2
                and len(_sentences(paragraphs[i + 1])) <= 2
                and _coin(prob)):
            result.append(p.rstrip() + ' ' + paragraphs[i + 1].lstrip())
            count += 1
            i += 2
        else:
            result.append(p)
            i += 1
    return '\n\n'.join(result), count


def marker_7_3(text: str, prob: int) -> tuple[str, int]:
    """Разбиение длинного абзаца."""
    count = 0
    paragraphs = text.split('\n\n')
    result = []
    for p in paragraphs:
        sents = _sentences(p)
        if len(sents) > 4 and _coin(prob):
            split_at = random.randint(2, len(sents) - 2)
            first = ' '.join(sents[:split_at])
            second = ' '.join(sents[split_at:])
            result.append(first + '\n\n' + second)
            count += 1
        else:
            result.append(p)
    return '\n\n'.join(result), count


def marker_7_4(text: str, prob: int) -> tuple[str, int]:
    """Лишняя пустая строка между абзацами."""
    count = 0
    paragraphs = text.split('\n\n')
    result = [paragraphs[0]] if paragraphs else []
    for p in paragraphs[1:]:
        if _coin(prob):
            result.append('\n' + p)
            count += 1
        else:
            result.append(p)
    return '\n\n'.join(result), count


# ═══════════════════════════════════════════════════
# 8. ЛЕКСИКА
# ═══════════════════════════════════════════════════

def marker_8_7(text: str, prob: int) -> tuple[str, int]:
    """Слэш вместо «или» (не в конструкции «или...или»)."""
    count = 0

    def repl(m):
        nonlocal count
        if _coin(prob):
            count += 1
            return m.group(1) + '/' + m.group(2)
        return m.group(0)

    # Не заменяем в конструкции «или ... или»
    result = re.sub(r'(\S+)\s+или\s+(\S+)(?!\s+или\b)', repl, text)
    return result, count


def marker_8_8(text: str, prob: int) -> tuple[str, int]:
    """Числительное → цифра (им./вин. падеж)."""
    count = 0
    num_map = {
        'один': '1', 'одна': '1', 'одно': '1',
        'два': '2', 'две': '2',
        'три': '3', 'четыре': '4', 'пять': '5',
        'шесть': '6', 'семь': '7', 'восемь': '8',
        'девять': '9', 'десять': '10',
    }
    for word, digit in num_map.items():
        pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)

        def make_repl(d):
            def inner(m):
                nonlocal count
                if _coin(prob):
                    count += 1
                    return d
                return m.group(0)
            return inner

        text = pattern.sub(make_repl(digit), text)
    return text, count


# ═══════════════════════════════════════════════════
# 10. ЭМОЦИОНАЛЬНЫЕ
# ═══════════════════════════════════════════════════

def marker_10_1(text: str, prob: int) -> tuple[str, int]:
    """Слово КАПСОМ (3-8 букв, макс 1 на абзац)."""
    count = 0
    paragraphs = text.split('\n\n')
    result_paragraphs = []

    for para in paragraphs:
        para_changed = False

        def repl(m):
            nonlocal count, para_changed
            word = m.group(0)
            if (not para_changed
                    and 3 <= len(word) <= 8
                    and word.islower()
                    and _coin(prob)):
                count += 1
                para_changed = True
                return word.upper()
            return word

        result_paragraphs.append(re.sub(r'[а-яё]{3,8}', repl, para))

    return '\n\n'.join(result_paragraphs), count


def marker_10_4(text: str, prob: int) -> tuple[str, int]:
    """Скобка-смайл ) в конце предложения вместо точки (макс 1-2 на текст)."""
    count = 0
    max_count = 2

    def repl(m):
        nonlocal count
        if count < max_count and _coin(prob):
            count += 1
            return ')'
        return m.group(0)

    # Заменяем точку в конце предложения (перед пробелом+заглавной или концом текста)
    result = re.sub(r'\.(?=\s+[А-ЯЁ]|$)', repl, text)
    return result, count


# ═══════════════════════════════════════════════════
# РЕЕСТР ФУНКЦИЙ (связь id → функция)
# ═══════════════════════════════════════════════════

MARKER_FUNCTIONS: dict[str, callable] = {
    # 1. Регистр и капитализация
    "1.1": marker_1_1, "1.2": marker_1_2, "1.3": marker_1_3,
    "1.4": marker_1_4, "1.6": marker_1_6,
    # 2. Лишние пробелы
    "2.1": marker_2_1, "2.2": marker_2_2, "2.3": marker_2_3,
    "2.4": marker_2_4, "2.5": marker_2_5, "2.6": marker_2_6,
    "2.7": marker_2_7, "2.8": marker_2_8, "2.9": marker_2_9,
    # 3. Пропущенные пробелы
    "3.1": marker_3_1, "3.2": marker_3_2, "3.3": marker_3_3,
    "3.4": marker_3_4,
    # 4. Пунктуация
    "4.1": marker_4_1, "4.2": marker_4_2, "4.3": marker_4_3,
    "4.4": marker_4_4, "4.5": marker_4_5, "4.6": marker_4_6,
    "4.7": marker_4_7, "4.8": marker_4_8, "4.9": marker_4_9,
    "4.10": marker_4_10, "4.11": marker_4_11, "4.12": marker_4_12,
    # 5. Кавычки, тире, типографика
    "5.1": marker_5_1, "5.2": marker_5_2, "5.3": marker_5_3,
    "5.4": marker_5_4, "5.5": marker_5_5, "5.6": marker_5_6,
    "5.7": marker_5_7, "5.8": marker_5_8, "5.9": marker_5_9,
    # 6. Опечатки набора
    "6.1": marker_6_1, "6.2": marker_6_2, "6.3": marker_6_3,
    "6.4": marker_6_4, "6.5": marker_6_5,
    # 7. Структура
    "7.2": marker_7_2, "7.3": marker_7_3, "7.4": marker_7_4,
    # 8. Лексика
    "8.7": marker_8_7, "8.8": marker_8_8,
    # 10. Эмоциональные
    "10.1": marker_10_1, "10.4": marker_10_4,
}

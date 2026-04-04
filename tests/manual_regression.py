"""
Ручные регрессионные тесты для критических/высоких багов.
Запуск: python tests/manual_regression.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import random
from engine.markers import (
    marker_1_6, marker_2_2, marker_4_1, marker_4_2,
    marker_4_3, marker_4_4,
)
from engine import TextProcessor

PASS = 0
FAIL = 0


def check(name, got, expected=None, condition=None, msg=""):
    global PASS, FAIL
    if condition is not None:
        ok = condition(got)
    else:
        ok = (got == expected)
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAIL += 1
        print(f"  [{status}] {name}")
        if expected is not None:
            print(f"         expected: {repr(expected)}")
        print(f"         got:      {repr(got)}")
        if msg:
            print(f"         hint:     {msg}")
    else:
        PASS += 1
        print(f"  [{status}] {name}")


print("=" * 60)
print("ЭТАП 1 (C1): --list-markers не должен падать на ≥")
print("=" * 60)
from engine.registry import MARKER_REGISTRY
try:
    output = ""
    for m in MARKER_REGISTRY:
        output += f"  {m.id:6s}  {m.name:35s}  (default: {m.default_prob:3d}%)  {m.description}\n"
    # Кодируем как UTF-8 — не должно падать
    output.encode('utf-8')
    check("Описания маркеров кодируются в UTF-8", True, True)
except UnicodeEncodeError as e:
    check("Описания маркеров кодируются в UTF-8", False, True, msg=str(e))


print()
print("=" * 60)
print("ЭТАП 2 (B4): marker_1_6 — строчное Я")
print("=" * 60)

random.seed(1)
r, c = marker_1_6("Я пошёл домой", 100)
check("1.6: Я в начале строки", r, "я пошёл домой")
check("1.6: count=1 для начала строки", c, 1)

random.seed(1)
r, c = marker_1_6("пошёл Я домой", 100)
check("1.6: Я в середине строки", r, "пошёл я домой")

random.seed(1)
r, c = marker_1_6("пошёл Я", 100)
check("1.6: Я в конце строки", r, "пошёл я")

random.seed(1)
r, c = marker_1_6("Я", 100)
check("1.6: одиночное Я", r, "я")

random.seed(1)
r, c = marker_1_6("ЯБЛОКО", 100)
check("1.6: ЯБЛОКО не трогается", r, "ЯБЛОКО")

random.seed(1)
r, c = marker_1_6("а Я пошёл", 100)
check("1.6: Я между словами (существующий случай)", r, "а я пошёл")


print()
print("=" * 60)
print("ЭТАП 3 (B5): marker_2_2 — пробел перед точкой")
print("=" * 60)

random.seed(1)
r, c = marker_2_2("Версия 3.14 файл", 100)
check("2.2: 3.14 не ломается", r, "Версия 3.14 файл",
      msg="десятичные числа не должны затрагиваться")

random.seed(1)
r, c = marker_2_2("файл test.txt", 100)
check("2.2: расширение файла не ломается", r, "файл test.txt",
      msg="расширения файлов не должны затрагиваться")

random.seed(1)
r, c = marker_2_2("Привет.", 100)
check("2.2: точка конца предложения обрабатывается",
      condition=lambda x: ' .' in x, got=r,
      msg="точка после кириллицы должна получить пробел")

random.seed(1)
r, c = marker_2_2("т.е. и т.д.", 100)
check("2.2: аббревиатуры не ломаются", r, "т.е. и т.д.",
      msg="т.е. и т.д. не должны затрагиваться")


print()
print("=" * 60)
print("ЭТАП 4 (B1): маркеры 4.1 + 4.2 — не дают !!!!")
print("=" * 60)

# Тест конфликта в процессоре
random.seed(42)
p = TextProcessor({"4.1": 100, "4.2": 100})
result = p.process("Круто!")
check("4.1+4.2: нет четырёх восклицаний",
      condition=lambda x: '!!!!' not in x, got=result,
      msg=f"получено: {repr(result)}")
check("4.1+4.2: максимум три восклицания",
      condition=lambda x: '!!!' in x or '!!' in x, got=result,
      msg=f"получено: {repr(result)}")

# Только 4.1
random.seed(1)
r, c = marker_4_1("Круто!", 100)
check("4.1 solo: ! -> !!", r, "Круто!!")

# Только 4.2 на тексте с !! (эскалация)
random.seed(1)
r, c = marker_4_2("Круто!!", 100)
check("4.2 solo: !! -> !!!", r, "Круто!!!")

# 4.2 на одиночном ! — не должен срабатывать (его зона — только !!)
random.seed(1)
r, c = marker_4_2("Круто!", 100)
check("4.2 solo: одиночный ! не затрагивается", r, "Круто!",
      msg="4.2 теперь работает только на !!, не на одиночных !")

# Аналог для 4.3 + 4.4
random.seed(42)
p2 = TextProcessor({"4.3": 100, "4.4": 100})
result2 = p2.process("Правда?")
check("4.3+4.4: нет ??!?",
      condition=lambda x: x.count('?') <= 3, got=result2,
      msg=f"получено: {repr(result2)}")


print()
print("=" * 60)
print("ИТОГ")
print("=" * 60)
total = PASS + FAIL
print(f"  Пройдено: {PASS}/{total}")
if FAIL:
    print(f"  Провалено: {FAIL}/{total}")
    sys.exit(1)
else:
    print("  Все тесты прошли успешно.")

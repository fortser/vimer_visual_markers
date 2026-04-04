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
print("СРЕДНИЙ ПРИОРИТЕТ — baseline (ожидаемые провалы до правок)")
print("=" * 60)

from engine.markers import marker_5_1, marker_5_2, marker_6_5
from engine.markers import marker_3_4, marker_5_3, marker_5_4, marker_5_5
from engine.registry import MARKER_REGISTRY, get_default_profile
from utils import load_profile, PROFILES_DIR
import os

# ── C2: save_profile с пустым dirname ────────────────────────
print()
print("C2: save_profile — пустой dirname")
import tempfile
from utils import save_profile
try:
    tmp = tempfile.mktemp(suffix='.json')
    bare = os.path.basename(tmp)
    orig_dir = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)
    save_profile(bare, {"name": "test"})
    check("C2: save_profile с bare filename не падает", True, True)
    os.remove(bare)
    os.chdir(orig_dir)
    os.rmdir(tmp_dir)
except Exception as e:
    os.chdir(orig_dir)
    check("C2: save_profile с bare filename не падает", False, True,
          msg=str(e))

# ── B8: registry default_prob совпадают с default.json ───────
print()
print("B8: registry vs default.json")
json_default = load_profile(str(PROFILES_DIR / 'default.json'))['markers']
reg_default = get_default_profile()
mismatches = [(mid, reg_default[mid], json_default[mid])
              for mid in reg_default if reg_default[mid] != json_default.get(mid)]
check("B8: registry default_prob совпадают с default.json",
      condition=lambda x: len(x) == 0, got=mismatches,
      msg=f"расхождений: {len(mismatches)} — {mismatches[:3]}...")

# ── B3: 3.4 работает после 5.3/5.4/5.5 ──────────────────────
print()
print("B3: маркер 3.4 не мёртв при 5.3/5.4/5.5")
from engine import TextProcessor
text_dash = '\u0441\u043b\u043e\u0432\u043e \u2014 \u0434\u0440\u0443\u0433\u043e\u0435'
random.seed(1)
p_b3 = TextProcessor({"5.3": 100, "5.4": 100, "5.5": 100, "3.4": 100})
r_b3 = p_b3.process(text_dash)
stats_b3 = p_b3.get_stats()
check("B3: 3.4 срабатывает при включённых 5.3/5.4/5.5",
      condition=lambda x: x.get("3.4", 0) > 0, got=stats_b3,
      msg=f"stats={stats_b3}, result={repr(r_b3)}")

# ── B6: marker_6_5 в начале/конце строки ─────────────────────
print()
print("B6: marker_6_5 — начало/конец строки")
random.seed(1)
r, c = marker_6_5("\u043e\u0447\u0435\u043d\u044c \u0445\u043e\u0440\u043e\u0448\u0438\u0439", 100)
check("B6: 'очень' в начале строки удваивается",
      condition=lambda x: x > 0, got=c,
      msg=f"count=0, result={repr(r)}")

random.seed(1)
r, c = marker_6_5("\u0445\u043e\u0440\u043e\u0448\u0438\u0439 \u043e\u0447\u0435\u043d\u044c", 100)
check("B6: 'очень' в конце строки удваивается",
      condition=lambda x: x > 0, got=c,
      msg=f"count=0, result={repr(r)}")

# ── B2: 5.1 + 5.2 при prob=100 ───────────────────────────────
print()
print("B2: 5.1 + 5.2 смешение кавычек")
text_q = '\u041e\u043d \u0441\u043a\u0430\u0437\u0430\u043b \u00ab\u043f\u0440\u0438\u0432\u0435\u0442\u00bb \u0438 \u00ab\u043f\u043e\u043a\u0430\u00bb \u0438 \u00ab\u0441\u043f\u0430\u0441\u0438\u0431\u043e\u00bb'
random.seed(1)
r51, c51 = marker_5_1(text_q, 100)
random.seed(1)
r52, c52 = marker_5_2(r51, 100)
check("B2: 5.2 срабатывает после 5.1 при prob=100/100",
      condition=lambda x: x > 0, got=c52,
      msg=f"c51={c51}, c52={c52}, result={repr(r52)}")

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

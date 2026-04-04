import sys, re, random
sys.stdout.reconfigure(encoding='utf-8')

# B2: тест порядка 5.1 / 5.2 с разными вероятностями
from engine.markers import marker_5_1, marker_5_2

text = 'Он сказал \u00abпривет\u00bb и \u00abпока\u00bb и \u00abспасибо\u00bb'

print("=== Текущий порядок: 5.1 -> 5.2 ===")
for p1, p2 in [(100, 100), (50, 50), (100, 0), (0, 100)]:
    random.seed(42)
    r, c1 = marker_5_1(text, p1)
    r, c2 = marker_5_2(r, p2)
    print(f"  5.1={p1} 5.2={p2}: {repr(r)} (c1={c1}, c2={c2})")

print()
print("=== Обратный порядок: 5.2 -> 5.1 ===")
for p1, p2 in [(100, 100), (50, 50), (100, 0), (0, 100)]:
    random.seed(42)
    r, c2 = marker_5_2(text, p2)
    r, c1 = marker_5_1(r, p1)
    print(f"  5.2={p2} 5.1={p1}: {repr(r)} (c2={c2}, c1={c1})")

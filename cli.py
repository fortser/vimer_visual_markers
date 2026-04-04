#!/usr/bin/env python3
"""
ВИМЕР — Визуальные Маркеры Естественной Речи
CLI Entry Point

Использование:
    python cli.py input.txt -o output.txt -p medium --stats
    python cli.py --list-profiles
    python cli.py --list-markers
    python cli.py input.txt  (профиль default, вывод в stdout)
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import TextProcessor, get_default_profile
from engine.registry import MARKER_REGISTRY, get_marker_by_id
from utils import (
    read_text_file, write_text_file, load_profile,
    list_profiles, PROFILES_DIR,
)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="ВИМЕР — добавляет маркеры естественного письма в текст.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="?", help="Входной файл (txt/md)")
    parser.add_argument("-o", "--output", help="Выходной файл (по умолчанию stdout)")
    parser.add_argument("-p", "--profile", default="default",
                        help="Имя профиля (default, light, medium, aggressive)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed для воспроизводимости")
    parser.add_argument("--multiplier", type=float, default=None,
                        help="Глобальный множитель (0.0-3.0)")
    parser.add_argument("--stats", action="store_true",
                        help="Статистика в stderr")
    parser.add_argument("--list-profiles", action="store_true",
                        help="Показать профили")
    parser.add_argument("--list-markers", action="store_true",
                        help="Показать все маркеры")
    parser.add_argument("--force", action="store_true",
                        help="Обрабатывать большие файлы")

    args = parser.parse_args()

    if args.list_profiles:
        profiles = list_profiles()
        if not profiles:
            print("Профили не найдены.")
        else:
            for p in profiles:
                prot = " [protected]" if p['protected'] else ""
                print(f"  {p['filename']:20s}  {p['name']:15s}  "
                      f"{p['description']}{prot}")
        return

    if args.list_markers:
        for m in MARKER_REGISTRY:
            print(f"  {m.id:6s}  {m.name:35s}  "
                  f"(default: {m.default_prob:3d}%)  {m.description}")
        return

    if not args.input:
        parser.error(
            "Укажите входной файл или используйте --list-profiles / --list-markers")

    try:
        text = read_text_file(args.input)
    except Exception as e:
        print(f"Ошибка чтения: {e}", file=sys.stderr)
        sys.exit(1)

    if len(text) > 5_000_000 and not args.force:
        print(f"Файл слишком большой ({len(text)} символов). "
              f"Используйте --force.", file=sys.stderr)
        sys.exit(1)

    profile_path = PROFILES_DIR / f"{args.profile}.json"
    if profile_path.exists():
        try:
            profile_data = load_profile(str(profile_path))
            markers = profile_data.get("markers", get_default_profile())
            multiplier = profile_data.get("multiplier", 1.0)
        except Exception as e:
            print(f"Ошибка профиля: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Профиль '{args.profile}' не найден, используется default.",
              file=sys.stderr)
        markers = get_default_profile()
        multiplier = 1.0

    if args.multiplier is not None:
        multiplier = args.multiplier

    processor = TextProcessor(markers, seed=args.seed, multiplier=multiplier)
    result = processor.process(text)

    if args.output:
        try:
            write_text_file(args.output, result)
            if args.stats:
                print(f"Сохранено: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка записи: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(result)

    if args.stats:
        stats = processor.get_stats()
        total = processor.get_total_changes()
        print(f"\n{'=' * 50}", file=sys.stderr)
        print(f"Всего изменений: {total}", file=sys.stderr)
        print(f"Активных маркеров: {len(stats)}", file=sys.stderr)
        for mid, cnt in sorted(stats.items()):
            info = get_marker_by_id(mid)
            name = info.name if info else mid
            print(f"  {mid:6s}  {name:35s}  x{cnt}", file=sys.stderr)


if __name__ == "__main__":
    main()

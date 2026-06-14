#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная фильтрация аниме по результатам AI-анализа.
"""

import json
from pathlib import Path


def get_min_age(age_str):
    """
    Извлекает минимальный возраст из строки.
    Поддерживает форматы: "18", "18-25"
    """
    if not age_str:
        return None

    try:
        if '-' in str(age_str):
            return int(age_str.split('-')[0].strip())
        return int(age_str)
    except (ValueError, AttributeError):
        return None


def filter_anime(
    anime_data,
    *,
    hero="female",
    violence="нет",
    mystical="нет",
    love_vibes="да",
    min_age=18,
):
    """
    Фильтрует аниме по критериям AI-анализа. Возвращает отфильтрованный словарь.

    Любой параметр можно задать как None — тогда этот критерий не проверяется.
    """
    print("\n" + "=" * 60)
    print("ФИНАЛЬНАЯ ФИЛЬТРАЦИЯ")
    print("=" * 60)

    filtered = {}

    for title, details in anime_data.items():
        if hero is not None and (details.get('hero') != hero and details.get('hero') != "unknown"):
            continue
        if violence is not None and details.get('violence') != violence:
            continue
        if mystical is not None and details.get('mystical') != mystical:
            continue
        if love_vibes is not None and details.get('love_vibes') != love_vibes:
            continue
        if min_age is not None:
            age = get_min_age(details.get('approximateage'))
            if age is None or age < min_age:
                continue

        filtered[title] = details

    original_count = len(anime_data)
    filtered_count = len(filtered)
    pct = filtered_count / original_count * 100 if original_count else 0

    print(f"Всего аниме: {original_count}")
    print(f"После фильтрации: {filtered_count}")
    print(f"Процент прошедших: {pct:.2f}%")
    print("=" * 60)

    return filtered


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "data/processed/filtered_with_ai.json"
    output_file = project_root / "data/results/final_anime.json"

    if not input_file.exists():
        print(f"Файл не найден: {input_file}")
    else:
        with open(input_file, 'r', encoding='utf-8') as f:
            anime_data = json.load(f)
        result = filter_anime(anime_data)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nРезультат сохранён в {output_file}")

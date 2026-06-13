#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт базовой фильтрации аниме.
Ожидает структурированную базу из 0_process_raw.py.
"""

import json
import re
from pathlib import Path


def is_sequel_or_continuation(anime_name):
    """Проверяет, является ли аниме продолжением/сезоном"""
    if '/' not in anime_name:
        return False

    russian_part = anime_name.split('/')[0].strip()

    patterns = [
        r'второй\s+сезон',
        r'третий\s+сезон',
        r'2\s+сезон',
        r'3\s+сезон',
    ]

    for pattern in patterns:
        if re.search(pattern, russian_part, re.IGNORECASE):
            return True

    continuation_keywords = [
        r'продолжение', r'финал', r'часть\s+\d+',
        r'final season', r'2nd season', r'3rd season'
    ]

    full_name_lower = anime_name.lower()
    for keyword in continuation_keywords:
        if re.search(keyword, full_name_lower):
            return True

    return False


def filter_basic(
    anime_dict,
    *,
    only_tv_series=True,
    exclude_sequels=True,
    exclude_rating_g=True,
    min_rating=6.0,
):
    """
    Базовая фильтрация аниме. Возвращает отфильтрованный словарь.
    """
    print("=" * 70)
    print("БАЗОВАЯ ФИЛЬТРАЦИЯ АНИМЕ")
    print("=" * 70)
    print(f"Всего аниме: {len(anime_dict)}")

    filtered = {}
    stats = {
        'not_tv': 0,
        'sequel': 0,
        'rating_g': 0,
        'low_score': 0
    }

    for anime_name, anime_data in anime_dict.items():
        if only_tv_series:
            if 'TV Сериал' not in anime_data.get('Тип', ''):
                stats['not_tv'] += 1
                continue

        rating_info = anime_data.get('Рейтинг')

        if exclude_sequels and is_sequel_or_continuation(anime_name):
            stats['sequel'] += 1
            continue

        if exclude_rating_g and rating_info == 'G':
            stats['rating_g'] += 1
            continue

        if min_rating is not None:
            rating_value = anime_data.get('rating')
            if rating_value is None:
                stats['low_score'] += 1
                continue
            try:
                if float(rating_value) < min_rating:
                    stats['low_score'] += 1
                    continue
            except (ValueError, TypeError):
                stats['low_score'] += 1
                continue

        filtered[anime_name] = dict(anime_data)

    print("\n" + "=" * 70)
    print("СТАТИСТИКА ФИЛЬТРАЦИИ")
    print("=" * 70)
    print(f"Исходное количество:           {len(anime_dict)}")
    if only_tv_series:
        print(f"Исключено не TV сериалов:      {stats['not_tv']}")
    if exclude_sequels:
        print(f"Исключено продолжений:         {stats['sequel']}")
    if exclude_rating_g:
        print(f"Исключено рейтинг G:           {stats['rating_g']}")
    if min_rating is not None:
        print(f"Исключено низкий рейтинг:      {stats['low_score']}")
    print(f"Итого осталось:                {len(filtered)}")
    print("=" * 70)

    return filtered


if __name__ == '__main__':
    input_file = 'data/processed/anime_database.json'
    output_file = 'data/processed/filtered_anime.json'

    if not Path(input_file).exists():
        print(f"Файл не найден: {input_file}")
        print("Сначала запустите: python src/0_process_raw.py")
    else:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        anime_dict = data.get('anime', data)
        result = filter_basic(anime_dict)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nРезультат сохранён в {output_file}")

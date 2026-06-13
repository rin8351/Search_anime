#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработка сырых данных: преобразование в структурированный формат.
Отфильтровывает только аниме без ключа description или с пустым описанием.
"""

import json
from pathlib import Path


def _append_field(entry, field_name, value):
    if not value:
        return
    if field_name in entry:
        entry[field_name] = f"{entry[field_name]} {value}".strip()
    else:
        entry[field_name] = value


def _transform_entry(anime_data):
    """Преобразует сырую запись в структурированный словарь."""
    info = anime_data.get('info', {})
    entry = {'description': anime_data['description']}

    for key in info:
        if key.startswith('Тип:'):
            entry['Тип'] = key.replace('Тип:', '').strip()
        elif key.startswith('Эпизоды:'):
            entry['Эпизоды'] = key.replace('Эпизоды:', '').strip()
        elif key.startswith('Жанры:') or key.startswith('Жанр:'):
            _append_field(entry, 'Жанры', key.split(':', 1)[1].strip())
        elif key.startswith('Рейтинг:'):
            entry['Рейтинг'] = key.replace('Рейтинг:', '').strip()
        elif key.startswith('Темы:') or key.startswith('Тема:'):
            _append_field(entry, 'Темы', key.split(':', 1)[1].strip())
        elif key.startswith('Статус:'):
            entry['Статус'] = key.replace('Статус:', '').strip()
        elif key.startswith('Длительность эпизода:'):
            entry['Длительность эпизода'] = key.replace('Длительность эпизода:', '').strip()
        elif key.startswith('Первоисточник:'):
            entry['Первоисточник'] = key.replace('Первоисточник:', '').strip()

    if 'rating' in anime_data:
        entry['rating'] = anime_data['rating']

    return entry


def _has_description(anime_data):
    if 'description' not in anime_data or anime_data['description'] == 'Нет описания':
        return False
    description = anime_data['description']
    return bool(description and description.strip())


def process_raw(anime_dict):
    """
    Преобразует сырые данные в структурированный формат.
    Исключает только записи без description или с пустым описанием.
    """
    print("=" * 70)
    print("ОБРАБОТКА СЫРЫХ ДАННЫХ")
    print("=" * 70)
    print(f"Всего аниме: {len(anime_dict)}")

    processed = {}
    skipped = 0

    for anime_name, anime_data in anime_dict.items():
        if not _has_description(anime_data):
            skipped += 1
            continue
        processed[anime_name] = _transform_entry(anime_data)

    print("\n" + "=" * 70)
    print("СТАТИСТИКА ОБРАБОТКИ")
    print("=" * 70)
    print(f"Исходное количество:           {len(anime_dict)}")
    print(f"Исключено без описания:        {skipped}")
    print(f"Итого в базе:                  {len(processed)}")
    print("=" * 70)

    return processed


def process_raw_file(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f"Файл не найден: {input_path}")
        return None

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    anime_dict = data.get('anime', data)
    result = process_raw(anime_dict)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nБаза сохранена в {output_path}")
    return result


if __name__ == '__main__':
    process_raw_file('data/raw/anime_database.json', 'data/processed/anime_database.json')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process raw data: convert to structured format.
Keeps only TV Сериал and Фильм, then only series originals
(earliest release in each group), then excludes entries without
description or with an empty description.
"""

import json
import re
from datetime import date
from pathlib import Path


MIN_VALID_YEAR = 1900
CONTINUATIONS_FILE = 'data/processed/anime_continuations.json'
ALLOWED_TYPES = frozenset({'TV Сериал', 'Фильм'})


def _append_field(entry, field_name, value):
    if not value:
        return
    if field_name in entry:
        entry[field_name] = f"{entry[field_name]} {value}".strip()
    else:
        entry[field_name] = value


def _strip_trailing_season_number(name):
    match = re.match(r'^(.*?)(\d+)\s*$', name)
    if match:
        base = match.group(1).strip()
        if base:
            return base
    return name


def _extract_base_name(anime_name):
    """
    Base name for grouping the same story:
    part before " / ", then before ":", then without trailing digit.
    """
    russian = anime_name.split(' / ', 1)[0].strip()
    if ':' in russian:
        russian = russian.split(':', 1)[0].strip()
    return _strip_trailing_season_number(russian)


def _get_status_from_raw(anime_data):
    for key in anime_data.get('info', {}):
        if key.startswith('Статус:'):
            return key.replace('Статус:', '').strip()
    return None


def _get_type_from_raw(anime_data):
    for key in anime_data.get('info', {}):
        if key.startswith('Тип:'):
            return key.replace('Тип:', '').strip()
    return None


def _extract_air_year(status):
    """
    Extract release year from the "Статус" field.
    Supports all patterns from analytic.json → status_patterns.
    """
    if not status:
        return None

    years = [int(match) for match in re.findall(r'\b(\d{4})\b', str(status))]
    valid_years = [
        year for year in years
        if MIN_VALID_YEAR <= year <= date.today().year + 1
    ]
    if not valid_years:
        return None

    return min(valid_years)


def _original_sort_key(anime_name, anime_dict):
    """Lower key = earlier release (preferred as original)."""
    status = _get_status_from_raw(anime_dict[anime_name])
    year = _extract_air_year(status)
    russian = anime_name.split(' / ', 1)[0].strip()
    has_subtitle = ':' in russian
    has_trailing_season = bool(re.search(r'\d+\s*$', russian.split(':', 1)[0]))
    return (
        year if year is not None else 9999,
        has_subtitle,
        has_trailing_season,
        anime_name,
    )


def _resolve_series(anime_dict):
    """
    Group anime by base name.
    Returns:
    - keep_names: original titles to keep in the database;
    - continuation_counts: {original: number of continuations};
    - continuations_map: {original: [list of continuations]} — only where continuations exist.
    """
    groups = {}
    for anime_name in anime_dict:
        base = _extract_base_name(anime_name)
        groups.setdefault(base, []).append(anime_name)

    keep_names = set()
    continuation_counts = {}
    continuations_map = {}

    for names in groups.values():
        if len(names) == 1:
            keep_names.add(names[0])
            continuation_counts[names[0]] = 0
            continue

        sorted_names = sorted(names, key=lambda name: _original_sort_key(name, anime_dict))
        original = sorted_names[0]
        continuations = sorted_names[1:]

        keep_names.add(original)
        continuation_counts[original] = len(continuations)
        continuations_map[original] = continuations

    return keep_names, continuation_counts, continuations_map


def _transform_entry(anime_data, continuation_count):
    """Convert a raw entry to a structured dictionary."""
    info = anime_data.get('info', {})
    entry = {'description': anime_data['description'], 'Продолжения': continuation_count}

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
    Convert raw data to structured format.
    Keeps only TV Сериал and Фильм, then only series originals,
    then excludes entries without description or with empty description.
    """
    print("=" * 70)
    print("RAW DATA PROCESSING")
    print("=" * 70)
    print(f"Total anime: {len(anime_dict)}")

    type_filtered = {}
    skipped_wrong_type = 0
    for anime_name, anime_data in anime_dict.items():
        if _get_type_from_raw(anime_data) in ALLOWED_TYPES:
            type_filtered[anime_name] = anime_data
        else:
            skipped_wrong_type += 1

    keep_names, continuation_counts, continuations_map = _resolve_series(type_filtered)
    skipped_continuation = len(type_filtered) - len(keep_names)

    processed = {}
    skipped_no_description = 0

    for anime_name, anime_data in type_filtered.items():
        if anime_name not in keep_names:
            continue
        if not _has_description(anime_data):
            skipped_no_description += 1
            continue
        processed[anime_name] = _transform_entry(
            anime_data,
            continuation_counts[anime_name],
        )

    print("\n" + "=" * 70)
    print("PROCESSING STATISTICS")
    print("=" * 70)
    print(f"Original count:                {len(anime_dict)}")
    print(f"Excluded by type:              {skipped_wrong_type}")
    print(f"Excluded (continuations):      {skipped_continuation}")
    print(f"Excluded (no description):     {skipped_no_description}")
    print(f"Total in database:             {len(processed)}")
    print("=" * 70)

    return processed, continuations_map


def process_raw_file(input_file, output_file, continuations_file=CONTINUATIONS_FILE):
    input_path = Path(input_file)
    output_path = Path(output_file)
    continuations_path = Path(continuations_file)

    if not input_path.exists():
        print(f"File not found: {input_path}")
        return None

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    anime_dict = data.get('anime', data)
    result, continuations_map = process_raw(anime_dict)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    continuations_path.parent.mkdir(parents=True, exist_ok=True)
    with open(continuations_path, 'w', encoding='utf-8') as f:
        json.dump(continuations_map, f, ensure_ascii=False, indent=2)

    print(f"\nDatabase saved to {output_path}")
    print(f"Continuations saved to {continuations_path}")
    return result


if __name__ == '__main__':
    process_raw_file('data/raw/anime_database.json', 'data/processed/anime_database.json')

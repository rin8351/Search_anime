#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Аналитика обработанной базы anime_database.json:
- уникальные ключи в записях аниме
- уникальные значения в полях Жанры и Темы
- уникальные значения Тип, Первоисточник, Статус
- паттерны названий (ключей): «Русское название / Английское название»
"""

import json
import re
from pathlib import Path


MONTH_PATTERN = re.compile(
    r'(?:'
    r'январ[ья]|янв\.?|'
    r'феврал[ья]|февр\.?|'
    r'марта?|мар\.?|'
    r'апрел[ья]|апр\.?|'
    r'ма[йя]\.?|'
    r'июн[ья]|июн\.?|'
    r'июл[ья]|июл\.?|'
    r'августа?|авг\.?|'
    r'сентябр[ья]|сент\.?|'
    r'октябр[ья]|окт\.?|'
    r'ноябр[ья]|нояб\.?|'
    r'декабр[ья]|дек\.?'
    r')',
    re.IGNORECASE,
)


def status_to_pattern(status: str) -> str:
    """Преобразует статус в шаблон, заменяя даты на day, mounth, year."""
    result = status

    result = re.sub(r'\b\d{4}-\d{4}\b', 'year-year', result)
    result = re.sub(r'\b\d{4}\b', 'year', result)
    result = re.sub(r'\b\d{1,2}\b', 'day', result)
    result = MONTH_PATTERN.sub('mounth', result)
    result = re.sub(r'\s*гг?\.?', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    result = re.sub(
        r'\bday mounth year\b',
        'day, mounth, year',
        result,
    )
    return result


def _collect_status_patterns(statuses: set[str]) -> list[str]:
    return sorted({status_to_pattern(status) for status in statuses})


STANDARD_TITLE_PATTERN = 'RU / EN'


def title_to_pattern(title: str) -> str:
    """
    Классифицирует ключ (название аниме) по структурному паттерну.
    Ожидаемый формат: «Русское название / Английское название».
    """
    parts = [part.strip() for part in title.split(' / ')]

    if len(parts) == 2 and parts[0] and parts[1]:
        return STANDARD_TITLE_PATTERN

    if ' / ' in title:
        return f'multiple_parts ({len(parts)})'

    if '/' in title:
        return 'slash without spaces'

    return 'no separator'


def _collect_title_patterns(titles: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for title in titles:
        pattern = title_to_pattern(title)
        if pattern == 'no separator':
            print('title without separator:',title)
        elif pattern == 'multiple_parts (3)':
            print('title with multiple parts:',title)
        counts[pattern] = counts.get(pattern, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _split_tokens(value: str) -> list[str]:
    """
    Разбивает строку на отдельные значения.
    Формат данных: пары через пробел (EN RU EN RU ...),
    например 'Shounen Сёнен Adventure Приключения'.
    """
    tokens = value.split()
    if not tokens:
        return []

    values: list[str] = []
    i = 0
    while i < len(tokens):
        if i + 1 < len(tokens):
            values.append(tokens[i])
            values.append(tokens[i + 1])
            i += 2
        else:
            values.append(tokens[i])
            i += 1
    return values


def collect_analytics(anime_dict: dict) -> dict:
    field_keys: set[str] = set()
    genres: set[str] = set()
    themes: set[str] = set()
    types: set[str] = set()
    sources: set[str] = set()
    statuses: set[str] = set()

    with_status = 0
    without_status = 0

    for anime_data in anime_dict.values():
        field_keys.update(anime_data.keys())

        if genre_value := anime_data.get('Жанры'):
            genres.update(_split_tokens(genre_value))

        if theme_value := anime_data.get('Темы'):
            themes.update(_split_tokens(theme_value))

        if type_value := anime_data.get('Тип'):
            types.add(type_value)

        if source_value := anime_data.get('Первоисточник'):
            sources.add(source_value)

        if status_value := anime_data.get('Статус'):
            statuses.add(status_value)
            with_status += 1
        else:
            without_status += 1

    title_patterns = _collect_title_patterns(list(anime_dict.keys()))
    matching_titles = title_patterns.get(STANDARD_TITLE_PATTERN, 0)

    return {
        'stats': {
            'total_anime': len(anime_dict),
            'total sources': len(sources),
            'total genres': len(genres),
            'total themes': len(themes),
            'total types': len(types),
            'titles_ru_en_pattern': matching_titles,
            'titles_other_patterns': len(anime_dict) - matching_titles,
        },
        'field_keys': sorted(field_keys),
        'status_patterns': _collect_status_patterns(statuses),
        'title_patterns': title_patterns,
        'sources': sorted(sources),
        'genres': sorted(genres),
        'themes': sorted(themes),
        'types': sorted(types)
    }


def analyze_database_file(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f'Файл не найден: {input_path}')
        return None

    print('=' * 70)
    print('АНАЛИТИКА ОБРАБОТАННОЙ БАЗЫ')
    print('=' * 70)

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    anime_dict = data.get('anime', data)
    result = collect_analytics(anime_dict)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    stats = result['stats']
    print(f"Всего аниме:              {stats['total_anime']}")
    print(f"Уникальных первоисточников:{stats['total sources']}")
    print(f"Уникальных жанров:        {stats['total genres']}")
    print(f"Уникальных тем:           {stats['total themes']}")
    print(f"Уникальных типов:         {stats['total types']}")
    print(f"Уникальных ключей:        {len(result['field_keys'])}")
    print(f"Уникальных паттернов:     {len(result['status_patterns'])}")
    print('-' * 70)
    print('Паттерны названий (ключей):')
    print(f"  {STANDARD_TITLE_PATTERN}: {stats['titles_ru_en_pattern']}")
    print(f"  Другие форматы:         {stats['titles_other_patterns']}")
    for pattern, count in result['title_patterns'].items():
        if pattern != STANDARD_TITLE_PATTERN:
            print(f"    {pattern}: {count}")
    print('=' * 70)
    print(f'\nРезультат сохранён в {output_path}')

    return result


if __name__ == '__main__':
    analyze_database_file(
        'data/processed/anime_database.json',
        'data/processed/analytic.json',
    )

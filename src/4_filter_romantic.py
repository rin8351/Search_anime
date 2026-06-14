import json
from pathlib import Path


def filter_romantic_anime(
    anime_data,
    *,
    excluded_genres=None,
    excluded_themes=None,
    required_genres=None,
    required_themes=None,
):
    """
    Фильтрует аниме по жанрам и темам. Возвращает отфильтрованный словарь.

    Логика:
    - хотя бы один жанр из required_genres (если список не пуст)
    - хотя бы одна тема из required_themes (если список не пуст)
    - ни одного жанра из excluded_genres
    - ни одной темы из excluded_themes
    """
    excluded_genres = excluded_genres or []
    excluded_themes = excluded_themes or []
    required_genres = required_genres or []
    required_themes = required_themes or []

    print("\n" + "=" * 60)
    print("ФИЛЬТРАЦИЯ ПО ЖАНРАМ И ТЕМАМ")
    print("=" * 60)
    print(f"Всего аниме: {len(anime_data)}")

    filtered_data = {}
    stats = {
        'total': len(anime_data),
        'filtered_by_required_genres': 0,
        'filtered_by_required_themes': 0,
        'filtered_by_excluded_genres': 0,
        'filtered_by_excluded_themes': 0,
    }

    for title, info in anime_data.items():
        genres_combined = info.get('Жанры', '')
        themes_combined = info.get('Темы', '')

        if required_genres:
            if not any(genre in genres_combined for genre in required_genres):
                stats['filtered_by_required_genres'] += 1
                continue

        if required_themes:
            if not any(theme in themes_combined for theme in required_themes):
                stats['filtered_by_required_themes'] += 1
                continue

        if excluded_genres:
            if any(genre in genres_combined for genre in excluded_genres):
                stats['filtered_by_excluded_genres'] += 1
                continue

        if excluded_themes:
            if any(theme in themes_combined for theme in excluded_themes):
                stats['filtered_by_excluded_themes'] += 1
                continue

        filtered_data[title] = info

    print("\n" + "=" * 60)
    print("СТАТИСТИКА ФИЛЬТРАЦИИ")
    print("=" * 60)
    print(f"Всего аниме в исходной базе:              {stats['total']}")
    if required_genres:
        print(f"Отфильтровано по обязательным жанрам:    {stats['filtered_by_required_genres']}")
    if required_themes:
        print(f"Отфильтровано по обязательным темам:     {stats['filtered_by_required_themes']}")
    if excluded_genres:
        print(f"Отфильтровано по исключаемым жанрам:     {stats['filtered_by_excluded_genres']}")
    if excluded_themes:
        print(f"Отфильтровано по исключаемым темам:       {stats['filtered_by_excluded_themes']}")
    print(f"Итоговое количество аниме:                {len(filtered_data)}")
    print("=" * 60)

    return filtered_data


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
    Filter anime by genres and themes. Returns a filtered dictionary.

    Logic:
    - at least one genre from required_genres (if the list is not empty)
    - at least one theme from required_themes (if the list is not empty)
    - no genres from excluded_genres
    - no themes from excluded_themes
    """
    excluded_genres = excluded_genres or []
    excluded_themes = excluded_themes or []
    required_genres = required_genres or []
    required_themes = required_themes or []

    print("\n" + "=" * 60)
    print("GENRE & THEME FILTERING")
    print("=" * 60)
    print(f"Total anime: {len(anime_data)}")

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
    print("FILTERING STATISTICS")
    print("=" * 60)
    print(f"Total in source database:                 {stats['total']}")
    if required_genres:
        print(f"Filtered by required genres:              {stats['filtered_by_required_genres']}")
    if required_themes:
        print(f"Filtered by required themes:               {stats['filtered_by_required_themes']}")
    if excluded_genres:
        print(f"Filtered by excluded genres:               {stats['filtered_by_excluded_genres']}")
    if excluded_themes:
        print(f"Filtered by excluded themes:               {stats['filtered_by_excluded_themes']}")
    print(f"Final count:                               {len(filtered_data)}")
    print("=" * 60)

    return filtered_data

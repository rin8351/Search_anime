#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт базовой фильтрации аниме.
Ожидает структурированную базу из 0_process_raw.py.
"""

import json
import re
from datetime import date
from pathlib import Path

MIN_VALID_YEAR = 1900

ANALYTIC_FILE = Path(__file__).resolve().parent.parent / "data/processed/analytic.json"


def _load_analytic_options():
    with open(ANALYTIC_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("types", []), data.get("sources", [])


def _validate_choice(value, valid_options, setting_name):
    """None — фильтр отключён. Неверные значения выводят предупреждение и дают None."""
    if value is None:
        return None

    if isinstance(value, str):
        if value in valid_options:
            return {value}
        print(
            f"Предупреждение: неверное значение «{value}» для «{setting_name}». "
            f"Допустимые варианты см. в data/processed/analytic.json. Фильтр отключён."
        )
        return None

    if isinstance(value, list):
        valid = []
        for item in value:
            if item in valid_options:
                valid.append(item)
            else:
                print(
                    f"Предупреждение: неверное значение «{item}» для «{setting_name}». "
                    f"Допустимые варианты см. в data/processed/analytic.json. "
                    f"Это значение проигнорировано."
                )
        if not valid:
            print(f"Предупреждение: для «{setting_name}» не осталось допустимых значений. Фильтр отключён.")
            return None
        return set(valid)

    print(
        f"Предупреждение: для «{setting_name}» ожидается None, str или list[str]. "
        f"Фильтр отключён."
    )
    return None


def _parse_episodes(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def _validate_year(value, setting_name):
    """None — фильтр отключён. Неверные значения выводят предупреждение и дают None."""
    if value is None:
        return None

    try:
        year = int(str(value).strip())
    except (ValueError, TypeError):
        print(
            f"Предупреждение: неверное значение «{value}» для «{setting_name}». "
            f"Ожидается целое число (год). Фильтр отключён."
        )
        return None

    current_year = date.today().year
    if year < MIN_VALID_YEAR or year > current_year:
        print(
            f"Предупреждение: неверное значение «{year}» для «{setting_name}». "
            f"Допустимый диапазон: {MIN_VALID_YEAR}–{current_year}. Фильтр отключён."
        )
        return None

    return year


def _extract_air_year(status):
    """
    Извлекает год выпуска из поля «Статус».
    Поддерживает все паттерны из analytic.json → status_patterns.
    Для диапазонов (например «в 2011-2014 гг.») берётся первый (минимальный) год.
    """
    if not status:
        return None

    years = [int(match) for match in re.findall(r"\b(\d{4})\b", str(status))]
    valid_years = [
        year for year in years
        if MIN_VALID_YEAR <= year <= date.today().year + 1
    ]
    if not valid_years:
        return None

    return min(valid_years)


def _split_title(anime_name):
    if " / " in anime_name:
        russian, english = anime_name.split(" / ", 1)
        return russian.strip(), english.strip()
    return anime_name.strip(), ""


def _normalize_title(title):
    return title.strip().casefold()


def is_watched(anime_name, watched_list):
    """Проверяет, есть ли аниме в списке просмотренных."""
    if not watched_list:
        return False

    russian, english = _split_title(anime_name)
    russian_norm = _normalize_title(russian)
    english_norm = _normalize_title(english)
    name_norm = _normalize_title(anime_name)

    for watched in watched_list:
        if not watched:
            continue
        watched = str(watched).strip()
        if not watched:
            continue

        watched_norm = _normalize_title(watched)
        if watched_norm == name_norm:
            return True

        w_russian, w_english = _split_title(watched)
        w_russian_norm = _normalize_title(w_russian)
        w_english_norm = _normalize_title(w_english)

        if w_english:
            if w_russian_norm == russian_norm and w_english_norm == english_norm:
                return True
            if w_russian_norm == russian_norm or w_english_norm == english_norm:
                return True
        elif watched_norm == russian_norm or watched_norm == english_norm:
            return True

    return False


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
    type_of_anime=None,
    source_material=None,
    exclude_sequels=True,
    exclude_rating_g=True,
    min_rating=6.0,
    min_episodes=None,
    max_episodes=None,
    min_year=None,
    max_year=None,
    watched_anime=None,
):
    """
    Базовая фильтрация аниме. Возвращает отфильтрованный словарь.
    """
    valid_types, valid_sources = _load_analytic_options()
    allowed_types = _validate_choice(type_of_anime, valid_types, "type_of_anime")
    allowed_sources = _validate_choice(source_material, valid_sources, "source_material")
    min_year = _validate_year(min_year, "min_year")
    max_year = _validate_year(max_year, "max_year")

    if min_year is not None and max_year is not None and min_year > max_year:
        print(
            f"Предупреждение: min_year ({min_year}) больше max_year ({max_year}). "
            f"Фильтр по году отключён."
        )
        min_year = None
        max_year = None

    print("=" * 70)
    print("БАЗОВАЯ ФИЛЬТРАЦИЯ АНИМЕ")
    print("=" * 70)
    print(f"Всего аниме: {len(anime_dict)}")

    filtered = {}
    stats = {
        "wrong_type": 0,
        "wrong_source": 0,
        "watched": 0,
        "sequel": 0,
        "rating_g": 0,
        "low_score": 0,
        "episodes": 0,
        "year": 0,
    }

    for anime_name, anime_data in anime_dict.items():
        if watched_anime and is_watched(anime_name, watched_anime):
            stats["watched"] += 1
            continue

        if allowed_types is not None:
            if anime_data.get("Тип") not in allowed_types:
                stats["wrong_type"] += 1
                continue

        if allowed_sources is not None:
            if anime_data.get("Первоисточник") not in allowed_sources:
                stats["wrong_source"] += 1
                continue

        rating_info = anime_data.get("Рейтинг")

        if exclude_sequels and is_sequel_or_continuation(anime_name):
            stats["sequel"] += 1
            continue

        if exclude_rating_g and rating_info == "G":
            stats["rating_g"] += 1
            continue

        if min_rating is not None:
            rating_value = anime_data.get("rating")
            if rating_value is None:
                stats["low_score"] += 1
                continue
            try:
                if float(rating_value) < min_rating:
                    stats["low_score"] += 1
                    continue
            except (ValueError, TypeError):
                stats["low_score"] += 1
                continue

        if min_episodes is not None or max_episodes is not None:
            episodes = _parse_episodes(anime_data.get("Эпизоды"))
            if episodes is None:
                stats["episodes"] += 1
                continue
            if min_episodes is not None and episodes < min_episodes:
                stats["episodes"] += 1
                continue
            if max_episodes is not None and episodes > max_episodes:
                stats["episodes"] += 1
                continue

        if min_year is not None or max_year is not None:
            air_year = _extract_air_year(anime_data.get("Статус"))
            if air_year is None:
                stats["year"] += 1
                continue
            if min_year is not None and air_year < min_year:
                stats["year"] += 1
                continue
            if max_year is not None and air_year > max_year:
                stats["year"] += 1
                continue

        filtered[anime_name] = dict(anime_data)

    print("\n" + "=" * 70)
    print("СТАТИСТИКА ФИЛЬТРАЦИИ")
    print("=" * 70)
    print(f"Исходное количество:           {len(anime_dict)}")
    if allowed_types is not None:
        types_label = ", ".join(sorted(allowed_types))
        print(f"Исключено по типу ({types_label}): {stats['wrong_type']}")
    if allowed_sources is not None:
        sources_label = ", ".join(sorted(allowed_sources))
        print(f"Исключено по первоисточнику ({sources_label}): {stats['wrong_source']}")
    if watched_anime:
        print(f"Исключено просмотренных:       {stats['watched']}")
    if exclude_sequels:
        print(f"Исключено продолжений:         {stats['sequel']}")
    if exclude_rating_g:
        print(f"Исключено рейтинг G:           {stats['rating_g']}")
    if min_rating is not None:
        print(f"Исключено низкий рейтинг:      {stats['low_score']}")
    if min_episodes is not None or max_episodes is not None:
        print(f"Исключено по числу эпизодов:   {stats['episodes']}")
    if min_year is not None or max_year is not None:
        year_range = []
        if min_year is not None:
            year_range.append(f"от {min_year}")
        if max_year is not None:
            year_range.append(f"до {max_year}")
        print(f"Исключено по году ({', '.join(year_range)}): {stats['year']}")
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
        result = filter_basic(anime_dict, type_of_anime="TV Сериал")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nРезультат сохранён в {output_file}")

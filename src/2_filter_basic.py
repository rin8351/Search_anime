#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт базовой фильтрации аниме

Шаг 1: Оставляет только TV сериалы с описаниями
Шаг 2: Фильтрует по рейтингам и убирает продолжения
"""

import json
import re
from pathlib import Path


def is_sequel_or_continuation(anime_name):
    """Проверяет, является ли аниме продолжением/сезоном"""
    if '/' not in anime_name:
        return False
    
    russian_part = anime_name.split('/')[0].strip()
    
    # Паттерны для поиска продолжений
    patterns = [
        r'\s+\d+\s*$',           # "Гинтама 4"
        r'\s+\d+\s*:',           # "Блич 2:"
        r'\s+[IVX]+\s*$',        # "Гинтама III"
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


def filter_basic(input_file, output_file, min_rating=6.0):
    """
    Базовая фильтрация аниме
    
    Фильтры:
    - Только TV сериалы
    - С описанием
    - Без продолжений
    - Рейтинг не G (детский)
    - Зрительский рейтинг >= min_rating
    """
    
    print("="*70)
    print("БАЗОВАЯ ФИЛЬТРАЦИЯ АНИМЕ")
    print("="*70)
    
    # Загрузка данных
    print(f"\nЗагрузка данных из {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    anime_dict = data.get('anime', data)
    print(f"Всего аниме: {len(anime_dict)}")
    
    # Фильтрация
    filtered = {}
    stats = {
        'not_tv': 0,
        'no_description': 0,
        'sequel': 0,
        'rating_g': 0,
        'low_score': 0
    }
    
    for anime_name, anime_data in anime_dict.items():
        # Проверка типа (TV сериал)
        info = anime_data.get('info', {})
        is_tv_series = any('TV Сериал' in key for key in info.keys() if key.startswith('Тип:'))
        
        if not is_tv_series:
            stats['not_tv'] += 1
            continue
        
        # Проверка описания
        description = anime_data.get('description', '')
        if (not description or not description.strip() or description.strip().lower() == "нет описания"):
            stats['no_description'] += 1
            continue
        
        # Извлечение полей
        episodes = None
        genres = None
        rating_info = None
        themes = None
        themes2 = None
        
        for key, value in info.items():
            if key.startswith('Эпизоды:'):
                episodes = key.replace('Эпизоды:', '').strip()
            elif key.startswith('Жанры:'):
                genres = key.replace('Жанры:', '').strip()
            elif key.startswith('Рейтинг:'):
                rating_info = key.replace('Рейтинг:', '').strip()
            elif key.startswith('Темы:'):
                themes = key.replace('Темы:', '').strip()
            elif key.startswith('Тема:'):
                themes2 = key.replace('Тема:', '').strip()
        
        # Создание упрощённой структуры
        new_entry = {
            'description': description
        }
        
        if episodes:
            new_entry['Эпизоды'] = episodes
        if genres:
            new_entry['Жанры'] = genres
        if rating_info:
            new_entry['Рейтинг'] = rating_info
        if themes:
            new_entry['Темы'] = themes
        if themes2:
            new_entry['Тема'] = themes2
        if 'rating' in anime_data:
            new_entry['rating'] = anime_data['rating']
        
        # Проверка на продолжение
        if is_sequel_or_continuation(anime_name):
            stats['sequel'] += 1
            continue
        
        # Проверка возрастного рейтинга
        if rating_info == 'G':
            stats['rating_g'] += 1
            continue
        
        # Проверка зрительского рейтинга
        rating_value = new_entry.get('rating')
        if rating_value is None:
            stats['low_score'] += 1
            continue
        
        try:
            rating_float = float(rating_value)
            if rating_float < min_rating:
                stats['low_score'] += 1
                continue
        except (ValueError, TypeError):
            stats['low_score'] += 1
            continue
        
        # Добавляем в результат
        filtered[anime_name] = new_entry
    
    # Сохранение
    print(f"\nСохранение результатов в {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    
    # Статистика
    print("\n" + "="*70)
    print("СТАТИСТИКА ФИЛЬТРАЦИИ")
    print("="*70)
    print(f"Исходное количество:           {len(anime_dict)}")
    print(f"Исключено не TV сериалов:      {stats['not_tv']}")
    print(f"Исключено без описания:        {stats['no_description']}")
    print(f"Исключено продолжений:         {stats['sequel']}")
    print(f"Исключено рейтинг G:           {stats['rating_g']}")
    print(f"Исключено низкий рейтинг:      {stats['low_score']}")
    print(f"Итого осталось:                {len(filtered)}")
    print("="*70)


if __name__ == '__main__':
    input_file = 'data/raw/anime_database.json'
    output_file = 'data/processed/filtered_anime.json'
    
    # Проверка существования входного файла
    if not Path(input_file).exists():
        print(f"❌ Файл не найден: {input_file}")
        print("Сначала запустите 1_parse_anime.py для сбора данных")
    else:
        filter_basic(input_file, output_file, min_rating=6.0)
        print(f"\n✅ Готово! Результат сохранён в {output_file}")

"""
Исходное количество:           20768
Исключено не TV сериалов:      13186
Исключено без описания:        4747
Исключено продолжений:         360
Исключено рейтинг G:           162
Исключено низкий рейтинг:      219
Итого осталось:                2094
"""
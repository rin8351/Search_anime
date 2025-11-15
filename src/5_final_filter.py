#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для фильтрации аниме по следующим критериям:
- hero: female
- violence: нет
- mystical: нет
- love_vibes: да
- approximateage: >= 18
"""

import json
from pathlib import Path


def load_anime_data(file_path):
    """Загружает данные аниме из JSON файла"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_min_age(age_str):
    """
    Извлекает минимальный возраст из строки.
    Поддерживает форматы: "18", "18-25"
    Возвращает None если возраст не указан или некорректен
    """
    if not age_str:
        return None
    
    try:
        # Если это диапазон (например "18-25"), берем первое число
        if '-' in str(age_str):
            min_age = int(age_str.split('-')[0].strip())
        else:
            # Если это одно число (например "22")
            min_age = int(age_str)
        return min_age
    except (ValueError, AttributeError):
        return None


def filter_anime(anime_data):
    """
    Фильтрует аниме по заданным критериям:
    - Главный герой женщина
    - Без насилия
    - Без мистики
    - С романтикой/любовным вайбом
    - Минимальный возраст >= 18
    """
    filtered = {}
    
    for title, details in anime_data.items():
        # Проверяем возраст
        min_age = get_min_age(details.get('approximateage'))
        age_ok = min_age is not None and min_age >= 18
        
        # Проверяем все критерии одновременно
        if (details.get('hero') == 'female' and
            details.get('violence') == 'нет' and
            details.get('mystical') == 'нет' and
            details.get('love_vibes') == 'да' and
            age_ok):
            
            filtered[title] = details
    
    return filtered


def save_filtered_data(filtered_data, output_file):
    """Сохраняет отфильтрованные данные в JSON файл"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)


def print_statistics(original_count, filtered_count):
    """Выводит статистику фильтрации"""
    print(f"\n{'='*60}")
    print(f"Статистика фильтрации:")
    print(f"{'='*60}")
    print(f"Всего аниме в исходном файле: {original_count}")
    print(f"Аниме после фильтрации: {filtered_count}")
    print(f"Процент прошедших фильтрацию: {filtered_count/original_count*100:.2f}%")
    print(f"{'='*60}\n")


def main():
    # Пути к файлам
    input_file = '../data/processed/filtered_with_ai.json'
    output_file = '../data/results/final_anime.json'
    
    print(f"Загружаем данные из {input_file}...")
    
    # Проверка существования входного файла
    if not Path(input_file).exists():
        print(f"ОШИБКА: Файл {input_file} не найден!")
        return
    
    # Загружаем данные
    anime_data = load_anime_data(input_file)
    original_count = len(anime_data)
    print(f"Загружено {original_count} аниме")
        
    filtered_data = filter_anime(anime_data)
    filtered_count = len(filtered_data)
    
    # Сохраняем результат
    save_filtered_data(filtered_data, output_file)
    print(f"\nРезультат сохранён в {output_file}")
    
    # Выводим статистику
    print_statistics(original_count, filtered_count)


if __name__ == "__main__":
    main()

"""
Всего аниме в исходном файле: 117
Аниме после фильтрации: 12
Процент прошедших фильтрацию: 10.26%
"""
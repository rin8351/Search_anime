#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для красивого вывода результатов анализа аниме
"""

import json
from pathlib import Path


def load_results(file_path='data/results/final_anime.json'):
    """Загружает результаты из JSON файла"""
    if not Path(file_path).exists():
        print(f"❌ Файл не найден: {file_path}")
        print("Убедитесь, что вы запустили весь pipeline.")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_anime_details(title, details, index):
    """Выводит детали одного аниме"""
    print(f"\n{'='*80}")
    print(f"#{index}. {title}")
    print(f"{'='*80}")
    
    # Основная информация
    print(f"Рейтинг: {details.get('rating', 'N/A')}")
    print(f"Эпизоды: {details.get('Эпизоды', 'N/A')}")
    print(f"Возраст героини: {details.get('approximateage', 'N/A')}")
    
    # Жанры и темы
    genres = details.get('Жанры', details.get('Жанр', 'N/A'))
    themes = details.get('Темы', details.get('Тема', 'N/A'))
    
    print(f"\nЖанры: {genres}")
    print(f"Темы: {themes}")
    
    # Возрастной рейтинг
    rating_age = details.get('Рейтинг', 'N/A')
    print(f"Возрастной рейтинг: {rating_age}")
    
    # AI-анализ
    print(f"\nAI-анализ:")
    print(f"   Главная роль: {'Женщина' if details.get('hero') == 'female' else details.get('hero', 'N/A')}")
    print(f"   Насилие: {'✅ Нет' if details.get('violence') == 'нет' else '❌ Да'}")
    print(f"   Мистика: {'✅ Нет' if details.get('mystical') == 'нет' else '❌ Да'}")
    print(f"   Фокус на романтике: {'💕 Да' if details.get('love_vibes') == 'да' else '❌ Нет'}")
    
    # Описание
    description = details.get('description', 'Нет описания')
    print(f"\nОписание:")
    print(f"   {description}")


def print_summary(anime_data):
    """Выводит краткую сводку"""
    print("\n" + "="*80)
    print("СТАТИСТИКА")
    print("="*80)
    
    total = len(anime_data)
    print(f"Всего найдено аниме: {total}")
    
    # Средний рейтинг
    ratings = [float(details['rating']) for details in anime_data.values() if 'rating' in details]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    print(f"Средний рейтинг: {avg_rating:.2f}")
    
    # Распределение по возрасту
    ages = {}
    for details in anime_data.values():
        age_range = details.get('approximateage', 'unknown')
        ages[age_range] = ages.get(age_range, 0) + 1
    
    print(f"\nРаспределение по возрасту героинь:")
    for age, count in sorted(ages.items()):
        print(f"   {age}: {count} аниме")
    
    # ТОП-3 по рейтингу
    sorted_anime = sorted(
        anime_data.items(),
        key=lambda x: float(x[1].get('rating', 0)),
        reverse=True
    )
    
    print(f"\nТОП-3 по рейтингу:")
    for i, (title, details) in enumerate(sorted_anime[:3], 1):
        print(f"   {i}. {title} ({details['rating']})")


def main():
    """Основная функция"""
    print("\n" + "="*80)
    print(" РЕЗУЛЬТАТЫ АНАЛИЗА АНИМЕ")
    print("="*80)
    
    # Загрузка данных
    anime_data = load_results()
    if not anime_data:
        return
    
    # Вывод краткой сводки
    print_summary(anime_data)
    
    # Меню
    while True:
        print("\n" + "="*80)
        print("МЕНЮ")
        print("="*80)
        print("1. Показать все аниме подробно")
        print("2. Показать список кратко")
        print("3. Показать конкретное аниме")
        print("4. Выход")
        
        choice = input("\nВыберите опцию (1-4): ").strip()
        
        if choice == '1':
            # Подробный вывод всех аниме
            for i, (title, details) in enumerate(anime_data.items(), 1):
                print_anime_details(title, details, i)
                if i < len(anime_data):
                    input("\nНажмите Enter для следующего аниме...")
        
        elif choice == '2':
            # Краткий список
            print("\n" + "="*80)
            print("СПИСОК АНИМЕ")
            print("="*80)
            for i, (title, details) in enumerate(anime_data.items(), 1):
                rating = details.get('rating', 'N/A')
                episodes = details.get('Эпизоды', 'N/A')
                print(f"{i}. {title} ({rating}, {episodes} эп.)")
        
        elif choice == '3':
            # Выбор конкретного аниме
            print("\nВведите номер аниме (1-{}): ".format(len(anime_data)), end='')
            try:
                num = int(input().strip())
                if 1 <= num <= len(anime_data):
                    title, details = list(anime_data.items())[num - 1]
                    print_anime_details(title, details, num)
                else:
                    print(" Неверный номер!")
            except ValueError:
                print("Введите число!")
        
        elif choice == '4':
            print("\n Спасибо за использование! Приятного просмотра!")
            break
        
        else:
            print("Неверный выбор! Попробуйте снова.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Программа прервана. До свидания!")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")


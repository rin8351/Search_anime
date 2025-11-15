import json


def has_romantic_genre(genres_str):
    """
    Проверяет, содержит ли строка жанров романтические жанры.
    Ищет: Романтика
    """
    if not genres_str:
        return False
    
    romantic_keywords = ['Романтика']
    
    for keyword in romantic_keywords:
        if keyword in genres_str:
            return True
    
    return False

def has_school_theme(themes_str):
    """
    Проверяет, содержит ли строка тем "Школа".
    """
    if not themes_str:
        return False
    
    return 'Школа' in themes_str

def has_supernatural_genre(genres_str):
    """
    Проверяет, содержит ли строка жанров "Сверхъестественное".
    """
    if not genres_str:
        return False
    
    return 'Сверхъестественное' in genres_str

def has_sci_fi_genre(genres_str):
    """
    Проверяет, содержит ли строка жанров "Научная фантастика".
    """
    if not genres_str:
        return False
    
    return 'Sci-Fi Фантастика' in genres_str

def has_fantasy_genre(genres_str):
    """
    Проверяет, содержит ли строка жанров "Фэнтези".
    """
    if not genres_str:
        return False
    
    return 'Фэнтези' in genres_str

def has_mahou_shoujo_theme(themes_str):
    """
    Проверяет, содержит ли строка тем "Махо-сёдзё".
    """
    if not themes_str:
        return False
    
    return 'Махо-сёдзё' in themes_str

def filter_romantic_anime(input_file, output_file):
    """
    Фильтрует аниме базу данных по романтическим жанрам и количеству эпизодов.
    
    Args:
        input_file: Путь к входному файлу JSON
        output_file: Путь к выходному файлу JSON
    """
    # Загрузка данных
    print(f"Загрузка данных из {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        anime_data = json.load(f)
    
    print(f"Всего аниме в базе: {len(anime_data)}")
    
    # Фильтрация
    filtered_data = {}
    stats = {
        'total': len(anime_data),
        'filtered_by_genre': 0,
        'filtered_by_school_theme': 0,
        'filtered_by_supernatural': 0,
        'filtered_by_sci_fi': 0,
        'filtered_by_fantasy': 0,
        'filtered_by_mahou_shoujo': 0,
        'final_count': 0
    }
    
    for title, info in anime_data.items():

        # Объединяем жанры и темы (могут быть в единственном и множественном числе)
        genres_combined = info.get('Жанр', '') + ' ' + info.get('Жанры', '')
        themes_combined = info.get('Тема', '') + ' ' + info.get('Темы', '')
        
        # Проверка жанра
        if not has_romantic_genre(genres_combined):
            stats['filtered_by_genre'] += 1
            continue
        
        # Исключение аниме с темой "Школа"
        if has_school_theme(themes_combined):
            stats['filtered_by_school_theme'] += 1
            continue
        
        # Исключение аниме с жанром "Сверхъестественное"
        if has_supernatural_genre(genres_combined):
            stats['filtered_by_supernatural'] += 1
            continue
        
        # Исключение аниме с жанром "Научная фантастика"
        if has_sci_fi_genre(genres_combined):
            stats['filtered_by_sci_fi'] += 1
            continue
        
        # Исключение аниме с жанром "Фэнтези"
        if has_fantasy_genre(genres_combined):
            stats['filtered_by_fantasy'] += 1
            continue
        
        # Исключение аниме с темой "Махо-сёдзё"
        if has_mahou_shoujo_theme(themes_combined):
            stats['filtered_by_mahou_shoujo'] += 1
            continue
        
        # Добавляем в отфильтрованные данные
        filtered_data[title] = info
    
    stats['final_count'] = len(filtered_data)
    
    # Сохранение результата
    print(f"\nСохранение отфильтрованных данных в {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    
    # Вывод статистики
    print("\n" + "="*60)
    print("СТАТИСТИКА ФИЛЬТРАЦИИ")
    print("="*60)
    print(f"Всего аниме в исходной базе:              {stats['total']}")
    print(f"Отфильтровано по жанру:                   {stats['filtered_by_genre']}")
    print(f"Отфильтровано по теме 'Школа':            {stats['filtered_by_school_theme']}")
    print(f"Отфильтровано по жанру 'Сверхъестеств.':  {stats['filtered_by_supernatural']}")
    print(f"Отфильтровано по жанру 'Научная фантастика': {stats['filtered_by_sci_fi']}")
    print(f"Отфильтровано по жанру 'Фэнтези':         {stats['filtered_by_fantasy']}")
    print(f"Отфильтровано по теме 'Махо-сёдзё':       {stats['filtered_by_mahou_shoujo']}")
    print(f"Итоговое количество аниме:                {stats['final_count']}")
    print("="*60)
    print(f"\nФайл успешно создан: {output_file}")

if __name__ == "__main__":
    input_file = "data/processed/filtered_anime.json"
    output_file = "data/processed/filtered_romantic.json"
    
    filter_romantic_anime(input_file, output_file)


"""
Статистика:
Всего аниме в исходной базе:              2094
Отфильтровано по жанру:                   1551
Отфильтровано по теме 'Школа':            240
Отфильтровано по жанру 'Сверхъестеств.':  46
Отфильтровано по жанру 'Научная фантастика': 59
Отфильтровано по жанру 'Фэнтези':         70
Отфильтровано по теме 'Махо-сёдзё':       11
Итоговое количество аниме:                117

"""


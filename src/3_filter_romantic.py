import json



def filter_romantic_anime(input_file, output_file):
    """
    Фильтрует аниме базу данных по заданным критериям жанров и тем.
    
    Логика фильтрации:
    - Аниме должно иметь хотя бы один жанр из get_required_genres_or()
    - Аниме должно иметь хотя бы одну тему из get_required_themes_or() (если список не пуст)
    - Аниме НЕ должно иметь ни одного жанра из get_excluded_genres()
    - Аниме НЕ должно иметь ни одной темы из get_excluded_themes()
    
    Args:
        input_file: Путь к входному файлу JSON
        output_file: Путь к выходному файлу JSON
    """
    # Списки для фильтрации
    excluded_genres = ['Сверхъестественное','Sci-Fi Фантастика','Фэнтези' ]
    excluded_themes = ['Школа','Махо-сёдзё']
    required_genres = ['Романтика']
    required_themes = []
    
    # Загрузка данных
    print(f"Загрузка данных из {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        anime_data = json.load(f)
    
    print(f"Всего аниме в базе: {len(anime_data)}")
       
    # Фильтрация
    filtered_data = {}
    stats = {
        'total': len(anime_data),
        'filtered_by_required_genres': 0,
        'filtered_by_required_themes': 0,
        'filtered_by_excluded_genres': 0,
        'filtered_by_excluded_themes': 0,
        'final_count': 0
    }
    
    for title, info in anime_data.items():
        # Объединяем жанры и темы (могут быть в единственном и множественном числе)
        genres_combined = info.get('Жанр', '') + ' ' + info.get('Жанры', '')
        themes_combined = info.get('Тема', '') + ' ' + info.get('Темы', '')
        
        # Проверка обязательных жанров (ИЛИ)
        if required_genres:
            has_required_genre = any(genre in genres_combined for genre in required_genres)
            if not has_required_genre:
                stats['filtered_by_required_genres'] += 1
                continue
        
        # Проверка обязательных тем (ИЛИ)
        if required_themes:
            has_required_theme = any(theme in themes_combined for theme in required_themes)
            if not has_required_theme:
                stats['filtered_by_required_themes'] += 1
                continue
        
        # Проверка исключаемых жанров
        if excluded_genres:
            has_excluded_genre = any(genre in genres_combined for genre in excluded_genres)
            if has_excluded_genre:
                stats['filtered_by_excluded_genres'] += 1
                continue
        
        # Проверка исключаемых тем
        if excluded_themes:
            has_excluded_theme = any(theme in themes_combined for theme in excluded_themes)
            if has_excluded_theme:
                stats['filtered_by_excluded_themes'] += 1
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
    if required_genres:
        print(f"Отфильтровано по обязательным жанрам:    {stats['filtered_by_required_genres']}")
    if required_themes:
        print(f"Отфильтровано по обязательным темам:     {stats['filtered_by_required_themes']}")
    if excluded_genres:
        print(f"Отфильтровано по исключаемым жанрам:     {stats['filtered_by_excluded_genres']}")
    if excluded_themes:
        print(f"Отфильтровано по исключаемым темам:       {stats['filtered_by_excluded_themes']}")
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
Отфильтровано по обязательным жанрам:    1551
Отфильтровано по исключаемым жанрам:     253
Отфильтровано по исключаемым темам:       173
Итоговое количество аниме:                117

"""


# -*- coding: utf-8 -*-
"""
Настройки pipeline: пути, фильтры и параметры AI-анализа.
"""

# =============================================================================
# НАСТРОЙКИ
# =============================================================================

# Пути к данным
PROCESSED_FILE = "data/processed/anime_database.json"
OUTPUT_FILE = "data/results/final_anime.json"

# Просмотренные аниме — исключаются на этапе 1.
# Ключи в anime_database.json имеют вид «Русское название / English title».
# Можно указать полный ключ или только русскую / английскую часть (точное совпадение).
WATCHED_ANIME = [
    "Твоя апрельская ложь",
]

# --- Этап 1: базовая фильтрация (3_filter_basic.py) ---
BASIC_FILTER = {
    # None — не фильтровать; str или list[str] — оставить указанные варианты.
    # Допустимые значения: data/processed/analytic.json → types
    "type_of_anime": "TV Сериал",
    # None — не фильтровать; str или list[str] — оставить указанные варианты.
    # Допустимые значения: data/processed/analytic.json → sources
    "source_material": None,
    "exclude_sequels": True,      # исключить продолжения/сезоны
    "exclude_rating_g": True,     # исключить детский рейтинг G
    "min_rating": 8.5,            # минимальный зрительский рейтинг (None — не проверять)
    "min_episodes": None,         # минимум эпизодов по ключу «Эпизоды» (None — не проверять)
    "max_episodes": None,         # максимум эпизодов по ключу «Эпизоды» (None — не проверять)
    # None — не фильтровать; int — год выпуска по ключу «Статус» (сравнение только по году).
    # Допустимые форматы дат: data/processed/analytic.json → status_patterns
    "min_year": None,             # минимальный год выпуска
    "max_year": 1980,             # максимальный год выпуска
}

# --- Этап 2: фильтр жанров и тем (3_filter_romantic.py) ---
Genre_FILTER = {
    #"excluded_genres": ["Fantasy", "Mystery","Сверхъестественное","Sci-Fi Фантастика","Фэнтези"], # исключить жанры
    "excluded_genres": [], # исключить жанры
    "excluded_themes": [], # исключить темы
    "required_genres": [], # включить жанры
    "required_themes": [], # включить темы
}

# --- Этап 3: AI-анализ (3_analyze_with_ai.py) ---
AI_CACHE_FILE = "data/cache/ai_analysis.json"  # None — отключить кэш
PROMPTS_DIR = "prompts"                          # папка с промптами (prompts/questions/*.txt)
ASK_BEFORE_AI = False       # спросить Да/Нет в терминале перед запросом к API
RUN_AI_ANALYSIS = False    # если ASK_BEFORE_AI = False: True — всегда, False — никогда

# --- Этап 4: финальная фильтрация (4_final_filter.py) ---
# None = критерий не применяется (и вопрос не отправляется в AI на этапе 3)
FINAL_FILTER = {
    "hero": "female",       # "female", "male", "unknown" или None
    "violence": "нет",      # "да", "нет" или None
    "mystical": "нет",      # "да", "нет" или None
    "love_vibes": "да",     # "да", "нет" или None
    "min_age": 18,          # минимальный возраст героя (None — не проверять)
}

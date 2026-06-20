# -*- coding: utf-8 -*-
"""
Pipeline settings: paths, filters, and AI analysis parameters.
"""

# =============================================================================
# SETTINGS
# =============================================================================

# Data paths
PROCESSED_FILE = "data/processed/anime_database.json"
OUTPUT_FILE = "data/results/final_anime.json"

# Already watched anime — excluded at stage 1.
# Keys in anime_database.json look like "Russian title / English title".
# You can specify the full key or only the Russian / English part (exact match).
WATCHED_ANIME = [
    "Твоя апрельская ложь",
]

# --- Stage 1: basic filtering (3_filter_basic.py) ---
BASIC_FILTER = {
    # None — no filter; str or list[str] — keep only listed values.
    # Valid values: TV Сериал, Фильм
    "type_of_anime": "TV Сериал",
    # None — no filter; str or list[str] — keep only listed values.
    # Valid values: data/processed/analytic.json → sources
    "source_material": None,
    # None — no filter; True — only with continuations; False — only without continuations
    "has_continuations": False,
    "exclude_rating_g": True,     # exclude G (children's) rating
    "min_rating": 7.5,            # minimum viewer score (None — skip check)
    "min_episodes": None,         # minimum episodes via "Эпизоды" key (None — skip check)
    "max_episodes": 50,         # maximum episodes via "Эпизоды" key (None — skip check)
    # None — no filter; int — release year from "Статус" key (year-only comparison).
    # Valid date formats: data/processed/analytic.json → status_patterns
    "min_year": 2000,             # minimum release year
    "max_year": None,             # maximum release year
}

# --- Stage 2: genre & theme filter (4_filter_romantic.py) ---
Genre_FILTER = {
    "excluded_genres": ["Fantasy", "Mystery","Сверхъестественное","Sci-Fi Фантастика","Фэнтези"],
    "excluded_themes": ["Школа"],
    "required_genres": ["Романтика"],
    "required_themes": [],
}

# --- Stage 3: AI analysis (5_analyze_with_ai.py) ---
AI_CACHE_FILE = "data/cache/ai_analysis.json"  # None — disable cache
PROMPTS_DIR = "prompts"                          # prompts folder (prompts/questions/*.txt)
ASK_BEFORE_AI = True       # ask Yes/No in terminal before API request
RUN_AI_ANALYSIS = False    # when ASK_BEFORE_AI = False: True — always, False — never

# --- Stage 4: final filtering (6_final_filter.py) ---
# None = criterion not applied (and the question is not sent to AI at stage 3)
# violence/mystical/love_vibes use Russian "да"/"нет" — that is what the AI returns
FINAL_FILTER = {
    "hero": "female",       # "female", "male", "unknown", or None
    "violence": "нет",      # "да", "нет", or None
    "mystical": "нет",      # "да", "нет", or None
    "love_vibes": "да",     # "да", "нет", or None
    "min_age": 18,          # minimum hero age (None — skip check)
}

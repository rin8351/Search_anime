#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа: запуск полного pipeline.

Все настройки — в config.py. Промежуточные JSON не создаются,
сохраняется только итоговый результат.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from config import (
    AI_CACHE_FILE,
    ASK_BEFORE_AI,
    BASIC_FILTER,
    FINAL_FILTER,
    Genre_FILTER,
    OUTPUT_FILE,
    PROCESSED_FILE,
    PROMPTS_DIR,
    RUN_AI_ANALYSIS,
    WATCHED_ANIME,
)


def _load_module(name: str, filename: str):
    path = Path(__file__).parent / "src" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ask_yes_no(prompt: str) -> bool:
    yes = {"да", "д", "yes", "y"}
    no = {"нет", "н", "no", "n"}

    while True:
        answer = input(f"{prompt} (Да/Нет): ").strip().lower()
        if answer in yes:
            return True
        if answer in no:
            return False
        print("Введите Да или Нет.")


def _should_run_ai_analysis(anime_count: int) -> bool:
    print("\n" + "=" * 60)
    print(f"После фильтрации осталось аниме: {anime_count}")
    print("=" * 60)

    if ASK_BEFORE_AI:
        if anime_count == 0:
            print("Нечего анализировать — AI-запрос пропущен.")
            return False
        return _ask_yes_no("Запустить AI-анализ описаний?")

    if not RUN_AI_ANALYSIS:
        print("AI-анализ отключён (ASK_BEFORE_AI = False).")
        return False
    if anime_count == 0:
        print("Нечего анализировать — AI-запрос пропущен.")
        return False
    print("AI-анализ включён (ASK_BEFORE_AI = False).")
    return True


def main():
    project_root = Path(__file__).resolve().parent
    output_path = project_root / OUTPUT_FILE

    load_dotenv(project_root / ".env")

    filter_basic_mod = _load_module("filter_basic", "3_filter_basic.py")
    filter_romantic_mod = _load_module("filter_romantic", "4_filter_romantic.py")
    analyze_ai_mod = _load_module("analyze_ai", "5_analyze_with_ai.py")
    final_filter_mod = _load_module("final_filter", "6_final_filter.py")

    print("Открытие обработанной базы...")
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        anime_dict = json.load(f)
    print(f"Всего аниме: {len(anime_dict)}\n")

    # Этап 1
    data = filter_basic_mod.filter_basic(anime_dict, watched_anime=WATCHED_ANIME, **BASIC_FILTER)

    # Этап 2
    data = filter_romantic_mod.filter_romantic_anime(data, **Genre_FILTER)

    ai_fields = analyze_ai_mod.fields_from_final_filter(FINAL_FILTER)

    if ai_fields and _should_run_ai_analysis(len(data)):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("API ключ не найден!")
            print("Создайте файл .env и добавьте: OPENAI_API_KEY=your_api_key_here")
            sys.exit(1)

        data = analyze_ai_mod.process_anime_database(
            data,
            api_key,
            fields=ai_fields,
            cache_file=AI_CACHE_FILE,
            prompts_dir=project_root / PROMPTS_DIR,
        )
        with open("data/processed/filtered_with_ai.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nРезультат сохранён в data/processed/filtered_with_ai.json")
        
        data = final_filter_mod.filter_anime(data, **FINAL_FILTER)
    elif not ai_fields:
        print("\nВсе критерии этапа 4 отключены — этапы 3–4 пропущены.")
    else:
        print("\nЭтапы 3–4 пропущены. Сохраняем результат после жанровой фильтрации.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nГотово! Итоговый результат ({len(data)} аниме) сохранён в {output_path}")


if __name__ == "__main__":
    main()

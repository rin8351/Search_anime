import hashlib
import json
import os
from pathlib import Path
from typing import Literal

import time
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, create_model

load_dotenv()

DEFAULT_CACHE_FILE = "data/cache/ai_analysis.json"
DEFAULT_PROMPTS_DIR = "prompts"

ANALYSIS_FIELDS = ("hero", "violence", "mystical", "love_vibes", "approximateage")

QUESTION_FILES = {
    "hero": "hero.txt",
    "violence": "violence.txt",
    "mystical": "mystical.txt",
    "love_vibes": "love_vibes.txt",
    "approximateage": "approximateage.txt",
}

FIELD_DEFAULTS = {
    "hero": "unknown",
    "violence": "нет",
    "mystical": "нет",
    "love_vibes": "нет",
    "approximateage": "unknown",
}

FIELD_LABELS = {
    "hero": "Герой",
    "violence": "Жестокость",
    "mystical": "Мистика",
    "love_vibes": "Любовь",
    "approximateage": "Возраст",
}


def fields_from_final_filter(final_filter: dict) -> list[str]:
    """Поля для AI-анализа: только те, что используются на этапе 4."""
    fields = []
    if final_filter.get("hero") is not None:
        fields.append("hero")
    if final_filter.get("violence") is not None:
        fields.append("violence")
    if final_filter.get("mystical") is not None:
        fields.append("mystical")
    if final_filter.get("love_vibes") is not None:
        fields.append("love_vibes")
    if final_filter.get("min_age") is not None:
        fields.append("approximateage")
    return fields


def _description_hash(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()


def load_analysis_cache(cache_file: Path) -> dict:
    if not cache_file.exists():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Не удалось загрузить кэш ({cache_file}): {e}")
        return {}


def save_analysis_cache(cache: dict, cache_file: Path) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cached_analysis(
    cache: dict,
    title: str,
    description: str,
    requested_fields: list[str],
) -> dict | None:
    entry = cache.get(title)
    if not entry:
        return None
    if entry.get("description_hash") != _description_hash(description):
        return None
    if entry.get("requested_fields") != requested_fields:
        return None
    return {field: entry[field] for field in requested_fields if field in entry}


def _create_analysis_model(fields: list[str]) -> type[BaseModel]:
    field_types = {
        "hero": (Literal["male", "female", "unknown"], ...),
        "violence": (Literal["да", "нет"], ...),
        "mystical": (Literal["да", "нет"], ...),
        "love_vibes": (Literal["да", "нет"], ...),
        "approximateage": (str, ...),
    }
    return create_model("AnimeAnalysis", **{field: field_types[field] for field in fields})


def build_prompt(
    title: str,
    description: str,
    fields: list[str],
    prompts_dir: Path,
) -> tuple[str, str]:
    system_prompt = (prompts_dir / "system.txt").read_text(encoding="utf-8").strip()
    intro = (prompts_dir / "user_intro.txt").read_text(encoding="utf-8")
    outro = (prompts_dir / "user_outro.txt").read_text(encoding="utf-8").strip()
    questions_dir = prompts_dir / "questions"

    question_parts = []
    for index, field in enumerate(fields, start=1):
        question_text = (questions_dir / QUESTION_FILES[field]).read_text(encoding="utf-8").strip()
        question_parts.append(f"{index}. {question_text}")

    user_prompt = intro.format(title=title, description=description)
    user_prompt += "\n".join(question_parts)
    user_prompt += f"\n{outro}"
    return system_prompt, user_prompt


def analyze_anime_with_ai(
    title: str,
    description: str,
    client: OpenAI,
    fields: list[str],
    prompts_dir: Path,
) -> tuple[dict, bool]:
    system_prompt, user_prompt = build_prompt(title, description, fields, prompts_dir)
    response_model = _create_analysis_model(fields)

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=response_model,
            temperature=0.3,
        )

        result = completion.choices[0].message.parsed
        return {field: getattr(result, field) for field in fields}, True

    except Exception as e:
        print(f"Ошибка при анализе '{title}': {e}")
        return {field: FIELD_DEFAULTS[field] for field in fields}, False


def _apply_analysis(anime_info: dict, analysis: dict) -> None:
    for field, value in analysis.items():
        anime_info[field] = value


def _print_analysis(analysis: dict) -> None:
    parts = [f"{FIELD_LABELS[field]}: {analysis[field]}" for field in analysis]
    print(f"  ✓ {', '.join(parts)}")


def process_anime_database(
    anime_data: dict,
    api_key: str,
    fields: list[str],
    cache_file: str | Path | None = DEFAULT_CACHE_FILE,
    prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
) -> dict:
    if not fields:
        print("\nВсе критерии этапа 4 отключены (None) — AI-анализ не требуется.")
        return anime_data

    client = OpenAI(api_key=api_key)
    cache_path = Path(cache_file) if cache_file else None
    cache = load_analysis_cache(cache_path) if cache_path else {}
    prompts_path = Path(prompts_dir)

    total_anime = len(anime_data)
    cached_count = 0
    api_count = 0

    print("\n" + "=" * 60)
    print("AI-АНАЛИЗ ОПИСАНИЙ")
    print("=" * 60)
    print(f"Аниме для анализа: {total_anime}")
    print(f"Поля для анализа: {', '.join(fields)}")
    if cache_path:
        print(f"Кэш: {cache_path}")
    print()

    processed_count = 0
    for title, anime_info in anime_data.items():
        processed_count += 1
        description = anime_info.get("description", "")
        print(f"[{processed_count}/{total_anime}] {title}")

        analysis = (
            get_cached_analysis(cache, title, description, fields)
            if cache_path
            else None
        )
        if analysis:
            cached_count += 1
            print("  ↺ из кэша")
            _apply_analysis(anime_info, analysis)
            _print_analysis(analysis)
            continue

        analysis, success = analyze_anime_with_ai(
            title, description, client, fields, prompts_path
        )
        _apply_analysis(anime_info, analysis)
        _print_analysis(analysis)

        if success and cache_path:
            api_count += 1
            cache[title] = {
                "description_hash": _description_hash(description),
                "requested_fields": fields,
                **analysis,
            }
            save_analysis_cache(cache, cache_path)
            time.sleep(0.5)
        elif not success:
            print("  ! ответ не сохранён в кэш из-за ошибки API")

    print(f"\nАнализ завершён: {total_anime} аниме")
    if cache_path:
        print(f"Из кэша: {cached_count}, новых запросов к API: {api_count}")
    return anime_data


def main():
    input_file = "data/processed/filtered_romantic.json"
    output_file = "data/processed/filtered_with_ai.json"

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("API ключ не найден!")
        print("Создайте файл .env и добавьте: OPENAI_API_KEY=your_api_key_here")
        return

    final_filter = {
        "hero": "female",
        "violence": "нет",
        "mystical": "нет",
        "love_vibes": "да",
        "min_age": 18,
    }
    fields = fields_from_final_filter(final_filter)

    with open(input_file, "r", encoding="utf-8") as f:
        anime_data = json.load(f)

    result = process_anime_database(anime_data, api_key, fields)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Результат сохранён в {output_file}")


if __name__ == "__main__":
    main()

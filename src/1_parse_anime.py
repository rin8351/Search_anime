#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Pipeline для сбора данных об аниме с shikimori.one

Этапы:
1. Extract: Загрузка списка URL аниме
2. Transform: Парсинг каждого аниме
3. Load: Сохранение в JSON базу данных

Usage:
    # Сначала получить список URL
    python fetch_anime_list.py -o anime_urls.json --max-pages 5
    
    # Затем запустить ETL pipeline
    python etl_pipeline.py -i anime_urls.json -o anime_database.json
    
    # С ограничением количества аниме (для теста)
    python etl_pipeline.py -i anime_urls.json -o anime_database.json --limit 10
"""

import argparse
import json
import sys
import time
from typing import List, Dict, Any
from pathlib import Path

from shikimori_parser import parse, HEADERS
import requests

def load_anime_urls(input_file: str) -> List[Dict[str, str]]:
    """Загрузить список URL аниме из JSON файла."""
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Поддержка разных форматов входных данных
    if isinstance(data, dict) and "anime" in data:
        return data["anime"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Неподдерживаемый формат входного файла")


def save_checkpoint(output_file: str, database: Dict[str, Any], processed_count: int):
    """Сохранить промежуточный результат (checkpoint)."""
    checkpoint_file = output_file.replace(".json", f"_checkpoint_{processed_count}.json")
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    return checkpoint_file


def run_etl_pipeline(
    input_file: str,
    output_file: str,
    limit: int = None,
    delay: float = 2.0,
    checkpoint_interval: int = 50,
    skip_first: int = 0
):
    """
    Запустить ETL pipeline для сбора данных об аниме.
    
    Args:
        input_file: путь к файлу со списком URL
        output_file: путь к выходному файлу базы данных
        limit: максимальное количество аниме для обработки
        delay: задержка между запросами в секундах
        checkpoint_interval: интервал сохранения промежуточных результатов
        skip_first: пропустить первые N аниме (для продолжения после ошибки)
    """
    
    print("="*70)
    print("ETL Pipeline: Сбор данных об аниме с shikimori.one")
    print("="*70)
    
    # EXTRACT: Загрузка списка URL
    print(f"\n[EXTRACT] Загрузка списка аниме из {input_file}...")
    anime_urls = load_anime_urls(input_file)
    total_anime = len(anime_urls)
    print(f"✓ Загружено {total_anime} аниме")
    
    # Применить skip_first и limit
    if skip_first > 0:
        anime_urls = anime_urls[skip_first:]
        print(f"[INFO] Пропущено первых {skip_first} аниме")
    
    if limit:
        anime_urls = anime_urls[:limit]
        print(f"[INFO] Ограничение: будет обработано {len(anime_urls)} аниме")
    
    # TRANSFORM & LOAD
    print(f"\n[TRANSFORM] Начало парсинга аниме...")
    print(f"Задержка между запросами: {delay} сек")
    print(f"Checkpoint каждые {checkpoint_interval} аниме\n")
    
    database = {}
    errors = []
    processed = 0
    
    start_time = time.time()
    
    for idx, anime_info in enumerate(anime_urls, start=1):
        url = anime_info.get("url")
        anime_id = anime_info.get("id", "unknown")
        
        print(f"[{idx}/{len(anime_urls)}] {url}...", end=" ")
        
        try:
            # Парсинг одного аниме
            anime_data = parse(url)
            database.update(anime_data)
            processed += 1
            print("✓")
            
            # Checkpoint
            if processed % checkpoint_interval == 0:
                checkpoint_file = save_checkpoint(output_file, database, processed)
                print(f"  → Checkpoint сохранен: {checkpoint_file}")
            
        except requests.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {url}"
            errors.append({"url": url, "id": anime_id, "error": str(e)})
            print(f"✗ {error_msg}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            errors.append({"url": url, "id": anime_id, "error": error_msg})
            print(f"✗ {error_msg}")
        
        # Задержка между запросами
        if idx < len(anime_urls):
            time.sleep(delay)
    
    # LOAD: Финальное сохранение
    print(f"\n[LOAD] Сохранение базы данных в {output_file}...")
    
    final_data = {
        "metadata": {
            "total_anime": len(database),
            "processed": processed,
            "errors": len(errors),
            "source": "shikimori.one",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "anime": database
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ База данных сохранена")
    
    # Сохранить отчет об ошибках
    if errors:
        error_file = output_file.replace(".json", "_errors.json")
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump({"errors": errors}, f, ensure_ascii=False, indent=2)
        print(f"✓ Лог ошибок сохранен: {error_file}")
    
    # Итоговая статистика
    elapsed = time.time() - start_time
    print("\n" + "="*70)
    print("СТАТИСТИКА")
    print("="*70)
    print(f"Обработано успешно: {processed}")
    print(f"Ошибки: {len(errors)}")
    print(f"Время выполнения: {elapsed/60:.1f} мин ({elapsed:.0f} сек)")
    if processed > 0:
        print(f"Среднее время на аниме: {elapsed/processed:.1f} сек")
    print("="*70)


def main():
    ap = argparse.ArgumentParser(
        description="ETL Pipeline для сбора данных об аниме"
    )
    ap.add_argument(
        "-i", "--input",
        required=True,
        help="Входной JSON файл со списком URL аниме"
    )
    ap.add_argument(
        "-o", "--output",
        default="anime_database.json",
        help="Выходной JSON файл для базы данных (по умолчанию: anime_database.json)"
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Максимальное количество аниме для обработки (для тестирования)"
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Задержка между запросами в секундах (по умолчанию: 2.0)"
    )
    ap.add_argument(
        "--checkpoint-interval",
        type=int,
        default=50,
        help="Интервал сохранения checkpoints (по умолчанию: каждые 50 аниме)"
    )
    ap.add_argument(
        "--skip-first",
        type=int,
        default=0,
        help="Пропустить первые N аниме (для продолжения после сбоя)"
    )
    
    args = ap.parse_args()
    
    # Проверка существования входного файла
    if not Path(args.input).exists():
        sys.stderr.write(f"[ERROR] Входной файл не найден: {args.input}\n")
        sys.stderr.write("Сначала запустите: python fetch_anime_list.py\n")
        sys.exit(1)
    
    # Запуск pipeline
    run_etl_pipeline(
        input_file=args.input,
        output_file=args.output,
        limit=args.limit,
        delay=args.delay,
        checkpoint_interval=args.checkpoint_interval,
        skip_first=args.skip_first
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Pipeline прерван пользователем")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"\n[ERROR] Критическая ошибка: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(2)


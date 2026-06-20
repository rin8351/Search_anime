#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL pipeline for collecting anime data from shikimori.one

Stages:
1. Extract: load list of anime URLs
2. Transform: parse each anime page
3. Load: save to JSON database

Usage:
    # First, obtain a URL list
    python fetch_anime_list.py -o anime_urls.json --max-pages 5

    # Then run the ETL pipeline
    python 1_parse_anime_site.py -i anime_urls.json -o anime_database.json

    # With a limit for testing
    python 1_parse_anime_site.py -i anime_urls.json -o anime_database.json --limit 10
"""

import argparse
import json
import sys
import time
from typing import List, Dict, Any
from pathlib import Path

from shikimori_parser import parse
import requests

def load_anime_urls(input_file: str) -> List[Dict[str, str]]:
    """Load anime URL list from a JSON file."""
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support different input formats
    if isinstance(data, dict) and "anime" in data:
        return data["anime"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unsupported input file format")


def save_checkpoint(output_file: str, database: Dict[str, Any], processed_count: int):
    """Save intermediate result (checkpoint)."""
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
    Run the ETL pipeline for anime data collection.

    Args:
        input_file: path to file with URL list
        output_file: path to output database file
        limit: maximum number of anime to process
        delay: delay between requests in seconds
        checkpoint_interval: interval for saving intermediate results
        skip_first: skip first N anime (to resume after failure)
    """

    print("="*70)
    print("ETL Pipeline: Collecting anime data from shikimori.one")
    print("="*70)

    # EXTRACT: load URL list
    print(f"\n[EXTRACT] Loading anime list from {input_file}...")
    anime_urls = load_anime_urls(input_file)
    total_anime = len(anime_urls)
    print(f"✓ Loaded {total_anime} anime")

    # Apply skip_first and limit
    if skip_first > 0:
        anime_urls = anime_urls[skip_first:]
        print(f"[INFO] Skipped first {skip_first} anime")

    if limit:
        anime_urls = anime_urls[:limit]
        print(f"[INFO] Limit: will process {len(anime_urls)} anime")

    # TRANSFORM & LOAD
    print(f"\n[TRANSFORM] Starting anime parsing...")
    print(f"Delay between requests: {delay} sec")
    print(f"Checkpoint every {checkpoint_interval} anime\n")

    database = {}
    errors = []
    processed = 0

    start_time = time.time()

    for idx, anime_info in enumerate(anime_urls, start=1):
        url = anime_info.get("url")
        anime_id = anime_info.get("id", "unknown")

        print(f"[{idx}/{len(anime_urls)}] {url}...", end=" ")

        try:
            # Parse a single anime page
            anime_data = parse(url)
            database.update(anime_data)
            processed += 1
            print("✓")

            # Checkpoint
            if processed % checkpoint_interval == 0:
                checkpoint_file = save_checkpoint(output_file, database, processed)
                print(f"  → Checkpoint saved: {checkpoint_file}")

        except requests.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {url}"
            errors.append({"url": url, "id": anime_id, "error": str(e)})
            print(f"✗ {error_msg}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            errors.append({"url": url, "id": anime_id, "error": error_msg})
            print(f"✗ {error_msg}")

        # Delay between requests
        if idx < len(anime_urls):
            time.sleep(delay)

    # LOAD: final save
    print(f"\n[LOAD] Saving database to {output_file}...")

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

    print(f"✓ Database saved")

    # Save error log
    if errors:
        error_file = output_file.replace(".json", "_errors.json")
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump({"errors": errors}, f, ensure_ascii=False, indent=2)
        print(f"✓ Error log saved: {error_file}")

    # Summary statistics
    elapsed = time.time() - start_time
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    print(f"Processed successfully: {processed}")
    print(f"Errors: {len(errors)}")
    print(f"Elapsed time: {elapsed/60:.1f} min ({elapsed:.0f} sec)")
    if processed > 0:
        print(f"Average time per anime: {elapsed/processed:.1f} sec")
    print("="*70)


def main():
    """
    CLI entry point for the ETL pipeline.

    Parses arguments, validates the input file, and runs
    run_etl_pipeline with the provided parameters.
    """
    ap = argparse.ArgumentParser(
        description="ETL pipeline for collecting anime data"
    )
    ap.add_argument(
        "-i", "--input",
        required=True,
        help="Input JSON file with anime URL list"
    )
    ap.add_argument(
        "-o", "--output",
        default="anime_database.json",
        help="Output JSON database file (default: anime_database.json)"
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of anime to process (for testing)"
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between requests in seconds (default: 2.0)"
    )
    ap.add_argument(
        "--checkpoint-interval",
        type=int,
        default=50,
        help="Checkpoint save interval (default: every 50 anime)"
    )
    ap.add_argument(
        "--skip-first",
        type=int,
        default=0,
        help="Skip first N anime (to resume after failure)"
    )

    args = ap.parse_args()

    # Check input file exists
    if not Path(args.input).exists():
        sys.stderr.write(f"[ERROR] Input file not found: {args.input}\n")
        sys.stderr.write("Run first: python fetch_anime_list.py\n")
        sys.exit(1)

    # Run pipeline
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
        print("\n\n[INFO] Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"\n[ERROR] Critical error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(2)

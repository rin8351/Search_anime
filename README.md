# Anime Finder: AI-Powered Anime Search & Filtering

> A pipeline for finding and filtering anime by custom criteria using the [shikimori.one](https://shikimori.one) database and OpenAI description analysis.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)

---

## About the Project

This project helps find anime matching very specific criteria from a database of **~20,000+** titles on Shikimori. Metadata (genres, themes, ratings) provides a rough shortlist, while AI analyzes **descriptions** where nuances not reflected in tags are hidden.

### Why is this needed?

A simple search by the "Romance" genre often falls short:

1. **Romance is often secondary** — the main plot may revolve around school, sports, or work, with relationships in the background.
2. **Genres and themes are not always accurate** — descriptions may contain mysticism, violence, or other elements missing from metadata.

**Examples:**
- *Wolf and Seven Friends* — harmless genres, but the description hints at danger and cruelty.
- *Chiko, Little Sister* — mysticism in the plot, though not listed in genres.

The pipeline combines classic filtering with AI-powered description analysis.

### Default criteria (configurable in `config.py`)

- Main heroine is an **adult woman** (18+)
- Plot is **focused on romance**
- **No mysticism or magic** (real-world setting)
- **No violence**
- TV series, rating ≥ 7.5, no sequels, released from 2000, up to 50 episodes

---

## Note on Language

This project was originally built for [shikimori.one](https://shikimori.one), a Russian-language anime database. Because of that:

- **Database field names and values** (genres, themes, types, etc.) remain in Russian — they come directly from the site.
- **Anime descriptions** in the database are in Russian.
- **AI prompts** in `prompts/` are kept in **Russian** on purpose: they analyze Russian descriptions, and the model returns more consistent results when the prompt language matches the text.
- **AI output values** are mixed by design:
  - `hero`: `male`, `female`, `unknown` (English)
  - `violence`, `mystical`, `love_vibes`: `да` / `нет` (Russian yes/no)
  - `approximateage`: numeric string or range (e.g. `"18"`, `"18-25"`)

If you fork this project for an English-language database, translate the prompts in `prompts/` and update `FINAL_FILTER` values in `config.py` accordingly.

### Prompt translations (reference)

The files in `prompts/` are in Russian. Below are English translations for reference.

**`prompts/system.txt`**
> You are an anime analysis expert. Answer accurately and in a structured way.

**`prompts/user_intro.txt`**
> Read the anime description and answer the questions:
> Anime title: {title}
> Description: {description}
> Questions:

**`prompts/user_outro.txt`**
> Analyze the description carefully and give a structured answer.

**`prompts/questions/hero.txt`**
> Who is the main character? Determine the gender of the main hero/heroine:
> - male (if the main character is a boy/man)
> - female (if the main character is a girl/woman)
> - unknown (if unclear, multiple main characters of different genders, or not enough information)

**`prompts/questions/violence.txt`**
> Is there cruelty or violence in the plot?
> - да (ONLY if explicitly mentioned: battles, murders, wars, combat, physical violence)
> - нет (character death, tragedy, illness, accident WITHOUT mention of violence = NO)

**`prompts/questions/mystical.txt`**
> Is there mysticism or magic in the plot?
> - да (if magic, supernatural, mysticism, or sorcery is mentioned)
> - нет (if none of the above is mentioned)

**`prompts/questions/love_vibes.txt`**
> What is the MAIN focus of the plot?
> - да (if the PRIMARY focus is developing romantic relationships between characters)
> - нет (if the focus is career, hobby, sport, work, school, adventure, with romance in the background)

**`prompts/questions/approximateage.txt`**
> State the age of one main hero/heroine if mentioned in the description.
> If not — estimate as a number or range based on the plot, characters' actions, work, school, or university.

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/yourusername/Search_anime.git
cd Search_anime

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

### 2. OpenAI API Key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Get a key: [OpenAI API Keys](https://platform.openai.com/api-keys)

### 3. Run Filtering

If the processed database already exists (`data/processed/anime_database.json`):

```bash
python main.py
```

The script runs all filtering stages in sequence. Before AI analysis (if `ASK_BEFORE_AI = True` in `config.py`), the program asks for confirmation in the terminal.

**Output:** `data/results/final_anime.json`

---

## Configuration

All filter parameters are in [`config.py`](config.py):

| Section | Purpose |
|---------|---------|
| `WATCHED_ANIME` | Already watched titles (excluded at stage 1) |
| `BASIC_FILTER` | Type, rating, episodes, year, continuations, G rating |
| `Genre_FILTER` | Required and excluded genres/themes |
| `FINAL_FILTER` | AI result criteria (hero gender, violence, mysticism, romance, age) |
| `ASK_BEFORE_AI` | Ask in terminal before calling the API |
| `RUN_AI_ANALYSIS` | Auto-run AI when `ASK_BEFORE_AI = False` |
| `AI_CACHE_FILE` | AI response cache (cheaper re-runs) |
| `PROMPTS_DIR` | Folder with AI prompts |

Valid values for `type_of_anime` and `source_material` are listed in `data/processed/analytic.json`.

**Important:** AI analyzes only fields actually used in `FINAL_FILTER`. If all stage 4 criteria are disabled (`None`), AI and final filtering stages are skipped.

---

## How the Pipeline Works

```
data/raw/anime_database.json
        │
        ▼
  Stage 0: process raw data (2_process_raw.py)
        │  → anime_database.json, anime_continuations.json
        ▼
  (optional) analyze database (analyze_raw.py)
        │  → analytic.json
        ▼
data/processed/anime_database.json
        │
        ▼
  Stage 1: basic filtering (3_filter_basic.py)
        │
        ▼
  Stage 2: genre & theme filter (4_filter_romantic.py)
        │
        ▼
  Stage 3: AI description analysis (5_analyze_with_ai.py)  ← optional
        │
        ▼
  Stage 4: final filtering (6_final_filter.py)
        │
        ▼
data/results/final_anime.json
```

Intermediate JSON files are **not created** during a normal run — only the final result is saved. If AI analysis runs, `data/processed/filtered_with_ai.json` is also written.

### Stage 1: Basic Filtering

- Anime type (TV series / film)
- Must have a description
- Exclude sequels and continuations
- Exclude G (children's) rating
- Minimum viewer score
- Episode count and release year range
- Exclude already watched titles

### Stage 2: Genres & Themes

- Required genres/themes (at least one from the list)
- Excluded genres/themes

### Stage 3: AI Analysis

- **Model:** OpenAI GPT-4o-mini
- **Prompts:** `prompts/` folder (questions in `prompts/questions/`)
- **Analyzed fields:**
  - Main character gender (`hero`)
  - Violence (`violence`)
  - Mysticism/magic (`mystical`)
  - Romance as plot focus (`love_vibes`)
  - Approximate hero age (`approximateage`)
- **Cache:** `data/cache/ai_analysis.json` — re-analyzing the same descriptions does not use tokens again

### Stage 4: Final Filtering

Select entries matching AI output values (or criteria set in `FINAL_FILTER`).

---

## Full Pipeline from Scratch

To build the database from the site:

```bash
# Stage 0a: parse anime pages (~10–15 hours for the full database)
# Requires: pip install requests beautifulsoup4
python src/1_parse_anime_site.py -i <url_list.json> -o data/raw/anime_database.json

# Stage 0b: process raw data → structured database
python src/2_process_raw.py

# Stages 1–4: filtering and AI
python main.py
```

Running `2_process_raw.py` with no arguments reads `data/raw/anime_database.json` and saves to `data/processed/anime_database.json`.

After processing, run analytics to explore the database before configuring filters:

```bash
python src/analyze_raw.py
```

---

## Processed Data Files

After stage 0b (`2_process_raw.py`), the `data/processed/` folder contains three key files:

| File | Created by | Purpose |
|------|------------|---------|
| `anime_database.json` | `2_process_raw.py` | Main working database for filtering |
| `anime_continuations.json` | `2_process_raw.py` | Map of originals → their continuations |
| `analytic.json` | `analyze_raw.py` | Database analytics for filter design |

### `anime_database.json`

The reformatted database used as input for `main.py`. Raw parser output is converted into a flat, analysis-friendly structure:

- **Removed:** nested `info` blocks, URLs, and other parser-specific fields not needed for filtering
- **Kept:** `description`, viewer `rating`, and metadata fields extracted from the site (`Тип`, `Эпизоды`, `Жанры`, `Темы`, `Рейтинг`, `Первоисточник`, `Статус`, etc.)
- **Added:** `Продолжения` — number of related sequels/spin-offs in the same story group (used by stage 1 to exclude titles with continuations)

Each entry is keyed by title in the format `"Russian title / English title"`.

Example record:

```json
{
  "Врата Штейна / Steins;Gate": {
    "description": "...",
    "Продолжения": 2,                                        // Number of continuations
    "Тип": "TV Сериал",                                      // Type (TV Series / Film)
    "Эпизоды": "24",                                         // Episode count
    "Статус": "с 6 апр. 2011 г. по 14 сент. 2011 г.",        // Status
    "Жанры": "Drama Драма Sci-Fi Фантастика ...",            // Genres
    "Темы": "Psychological Психологическое Time Travel ...", // Themes
    "Рейтинг": "PG-13",                                      // Age rating
    "Первоисточник": "Визуальная новелла",                   // Source material
    "rating": "9.07"                                         // Viewer score
  }
}
```

**Note:** `rating` (lowercase) is the viewer score from Shikimori (e.g. `9.07`) — used by `BASIC_FILTER.min_rating`. `Рейтинг` is the age rating from the site (e.g. `G`, `PG-13`) — used by `BASIC_FILTER.exclude_rating_g`.


During stage 0b, the script also:
- keeps only TV Сериал (TV Series) and Фильм (Film)
- groups multi-season titles and keeps the **earliest release** as the original
- drops entries without a description

### `anime_continuations.json`

A sidecar file produced alongside `anime_database.json`. Maps each **original** title to a list of its **continuations** (sequels, later seasons, related films in the same story group):

```json
{
  "Врата Штейна / Steins;Gate": [
    "Врата Штейна: Зона загрузки дежавю / Steins;Gate Movie: ...",
    "Врата Штейна 0 / Steins;Gate 0"
  ]
}
```

Useful for inspecting which titles were merged during processing. The `Продолжения` count in `anime_database.json` is derived from this grouping.

### `analytic.json`

A summary of the processed database, generated by `analyze_raw.py`. Use it to see what filter values are valid before editing `config.py`:

- **`sources`** — all unique `Первоисточник` values (for `BASIC_FILTER.source_material`)
- **`types`** — all unique `Тип` values (for `BASIC_FILTER.type_of_anime`)
- **`genres`** / **`themes`** — all unique genre and theme tokens (for `Genre_FILTER`)
- **`status_patterns`** — date format templates found in `Статус` (helps understand year extraction in stage 1)
- **`field_keys`** — all field names present in records
- **`title_patterns`** — how title keys are structured (mostly `"RU / EN"`)
- **`stats`** — counts: total anime, unique genres/themes/types/sources, title format breakdown

---

## Database Analytics (`analyze_raw.py`)

Before writing filters, it helps to understand what is actually in the database. The `analyze_raw.py` script scans `anime_database.json` and writes a structured report to `analytic.json`.

```bash
python src/analyze_raw.py
```

**What it counts and why:**

| Output | What it shows | Why it matters |
|--------|---------------|----------------|
| `genres`, `themes` | Every distinct genre/theme token | Pick valid values for `Genre_FILTER.required_genres` and `excluded_genres` |
| `types` | Every anime type (`TV Сериал`, `Фильм`, …) | Set `BASIC_FILTER.type_of_anime` correctly |
| `sources` | Every source material type | Set `BASIC_FILTER.source_material` if needed |
| `status_patterns` | Date formats in the `Статус` field | Stage 1 extracts release year from these strings — patterns show what formats exist |
| `field_keys` | All keys used in records | Verify which metadata fields are available for filtering |
| `title_patterns` | Title key structure (`RU / EN`, etc.) | Understand how titles are stored; useful for `WATCHED_ANIME` matching |
| `stats` | Totals and breakdowns | Quick overview of database size and diversity |

The script also prints a summary to the terminal. Re-run it whenever you rebuild `anime_database.json` — filter options in `config.py` should match the values listed in `analytic.json`.

---

## Project Structure

```
Search_anime/
├── main.py                    # Entry point: run the full pipeline
├── config.py                  # All filter and AI settings
│
├── src/
│   ├── 1_parse_anime_site.py  # Parse shikimori.one
│   ├── 2_process_raw.py       # Process raw data
│   ├── 3_filter_basic.py      # Basic filtering
│   ├── 4_filter_romantic.py   # Genre & theme filter
│   ├── 5_analyze_with_ai.py   # AI description analysis
│   ├── 6_final_filter.py      # Final selection
│   ├── analyze_raw.py         # Database analytics helper
│   └── shikimori_parser.py    # Single-page parsing utility
│
├── prompts/                   # AI prompts (Russian — see Note on Language)
│   ├── system.txt
│   ├── user_intro.txt
│   ├── user_outro.txt
│   └── questions/
│       ├── hero.txt
│       ├── violence.txt
│       ├── mystical.txt
│       ├── love_vibes.txt
│       └── approximateage.txt
│
├── data/
│   ├── raw/
│   │   └── anime_database.json       # Raw parser output
│   ├── processed/
│   │   ├── anime_database.json       # Reformatted database (pipeline input)
│   │   ├── anime_continuations.json  # Original → continuations map
│   │   └── analytic.json             # Database analytics (from analyze_raw.py)
│   ├── cache/
│   │   └── ai_analysis.json          # AI response cache
│   └── results/
│       └── final_anime.json          # Final filtered result
│
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Technologies

- **Python 3.8+**
- **OpenAI API (GPT-4o-mini)** — description analysis
- **Pydantic** — structured AI response validation
- **python-dotenv** — API key storage
- **Beautiful Soup 4 + requests** — site parsing (data collection stage only)

---

## AI Analysis Cost

Approximate costs with GPT-4o-mini:

| Volume | Approximate cost |
|--------|------------------|
| ~100 anime after filters | $0.10–0.20 |
| ~2,000 anime | ~$2 |
| ~20,000 anime without pre-filtering | ~$20+ |

Pre-filtering by genres and metadata significantly reduces cost. The cache in `data/cache/` avoids paying again for already analyzed descriptions.

---

## Security

The `.env` file with your API key is listed in `.gitignore` and is not committed to the repository.

**Do not commit:** API keys, passwords, tokens, or personal data.

---

## License

MIT License — use freely.

---

## Acknowledgments

- [Shikimori.one](https://shikimori.one) — anime database
- [OpenAI](https://openai.com) — text analysis API

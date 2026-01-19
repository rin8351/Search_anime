# Anime Finder: Finding the Perfect Anime with AI

> Automated pipeline for filtering anime by specific criteria using AI

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)

---

## About the Project

This project solves the task of finding anime by very specific criteria from a database of **20,000+ anime** from [shikimori.one](https://shikimori.one).
Almost every anime on the site has: genre, theme, description. Filtering was done based on these.

### Target Criteria:
- Main heroine is an **adult girl** (18+ years old)
- Plot is **focused on romance** and relationship development
- Events take place in the **real world** (no magic/mysticism)
- No elements of **violence and cruelty**

###  Why is this project needed?

A simple search by the "Romance" genre on the site didn't yield the desired results for two reasons:
1. **The "Romance" genre is often secondary.** Even if it's listed, the main plot may be built around sports, studies, work, or hobbies of the characters, with romance as a background. I needed **romance as the basis of the plot**.
2. **Genres and themes are not always accurate.** Elements of mysticism, magic, or cruelty may be present in the anime description, even if not explicitly indicated in the metadata.

**Examples:**
- *"Wolf and Seven Friends"* — genres are harmless, but the description hints at danger and cruelty
- *"Chiko, Little Sister"* — there's mysticism in the plot, although not indicated in genres

Therefore, a pipeline with AI analysis of descriptions was created for accurate filtering.

### Result:
**20,771 anime** → **12 perfect matches** (reduction rate: 99.94%)

---

## Note on AI Prompt Language

**Important:** The AI prompt used in this project (in `src/4_analyze_with_ai.py`) is currently written in **Russian**, as this is the language the project was originally used in. The prompt analyzes anime descriptions in Russian. If you want to use this project with English descriptions or prompts, you may need to translate the prompt accordingly.

---

## Project Structure

```
Search_anime/
├── src/                              # All code
│   ├── 1_parse_anime.py             # Parsing from shikimori.one
│   ├── 2_filter_basic.py            # Basic filtering
│   ├── 3_filter_romantic.py         # Romance filter
│   ├── 4_analyze_with_ai.py         # AI analysis of descriptions
│   ├── 5_final_filter.py            # Final selection
│   ├── shikimori_parser.py          # Parsing utility
│   └── view_results.py              # Interactive viewing
│
├── data/                             # Data (not in Git)
│   ├── raw/                         # Raw data
│   ├── processed/                   # Intermediate results
│   └── results/                     # Final results
│       └── final_anime.json         #  12 anime
│
├── README.md                         # English version
├── README_RU.md                      # Russian version
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Full Pipeline (from scratch)

If you want to run the entire process from parsing to result:

```bash
cd src

# Stage 1: Parsing (~10-15 hours for all anime)
python 1_parse_anime.py

# Stage 2: Basic filtering (TV series, rating ≥6.0)
python 2_filter_basic.py

# Stage 3: Romance filtering (genres, themes)
python 3_filter_romantic.py

# Stage 4: AI analysis (~5-10 minutes, ~$0.10-0.20)
python 4_analyze_with_ai.py

# Stage 5: Final filtering
python 5_final_filter.py

# View results
python view_results.py
```

---

## How the Pipeline Works

### Stage 1: Data Parsing
- **Input:** shikimori.one
- **Output:** `data/raw/anime_database.json` (20,771 anime)
- **What is extracted:** titles, descriptions, genres, ratings, episodes

### Stage 2: Basic Filtering
- **Filters:**
  - ✅ TV series only
  - ✅ Has description
  - ❌ Excluded sequels/continuations
  - ❌ Excluded G rating (children's)
  - ⭐ Viewer rating ≥ 6.0
- **Result:** 2,089 anime

### Stage 3: Romance Filtering
- **Filters:**
  - ✅ Genre: Romance
  - ❌ Excluded theme: School
  - ❌ Excluded genres: Supernatural, Fantasy, Sci-Fi, Mahou Shoujo
- **Result:** 117 anime

### Stage 4: AI Analysis of Descriptions
- **Model:** OpenAI GPT-4o-mini
- **Analyzed:**
  - Main character's gender
  - Presence of violence
  - Presence of mysticism/magic
  - Romance as the basis of the plot
  - Main character's age

### Stage 5: Final Selection
- **Criteria:**
  - ✅ hero = "female"
  - ✅ violence = "нет" (no)
  - ✅ mystical = "нет" (no)
  - ✅ love_vibes = "да" (yes)
  - ✅ approximateage ≥ 18
- **Result:** 12 anime ✨

---

##  Technologies

- **Python 3.8+** — programming language
- **Beautiful Soup 4** — HTML parsing
- **OpenAI API (GPT-4o-mini)** — description analysis
- **Pydantic** — structured response validation
- **python-dotenv** — secure API key storage

---

##  Cost

When using OpenAI GPT-4o-mini:
- **117 anime** (final filtering): ~$0.10-0.20
- **2,089 anime** (if run earlier): ~$2.15
- **20,000+ anime** (if without filters): ~$21.40

**Savings from pre-filtering: >$19**

---

## Requirements

- Python 3.8 or higher
- OpenAI API key (for AI analysis)
- ~500 MB free space (for full database)

---

##  Security

⚠️ **Important:** The `.env` file with the API key is already added to `.gitignore` and will not be uploaded to Git.

**Never commit:**
- API keys
- Passwords
- Tokens
- Personal data

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Search_anime.git
cd Search_anime

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. API Key Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Get a key: [OpenAI API Keys](https://platform.openai.com/api-keys)

### 3. Running (with ready data)

If you already have filtered data:

```bash
cd src

# AI analysis (requires API key, ~5-10 minutes, ~$0.10-0.20)
python 4_analyze_with_ai.py

# Final filtering
python 5_final_filter.py

# View results
python view_results.py
```

---

## License

MIT License — feel free to use!

---

##  Acknowledgments

- [Shikimori.one](https://shikimori.one) — anime database
- [OpenAI](https://openai.com) — API for text analysis

---
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер страниц аниме «Шикимори»
Использование:

python shikimori_parser.py https://shikimori.one/animes/5680-k-on -o k_on.json

Что извлекает:
- Заголовок (из <header> <h1> или meta[itemprop="name"/"headline"])
- Блок «Информация» (из div.c-about -> div.b-entry-info -> div.line-container)
- Рейтинг (использует микроданные meta[itemprop="ratingValue"], затем видимую оценку рядом с «РЕЙТИНГ»)
- Описание (из div.c-description > div.description-current ИЛИ div[itemprop="description"])
"""

import argparse
import json
import re
import sys
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup, Tag

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru,en;q=0.9",
}


def fetch_html(url: str) -> str:
    """
    Загружает HTML содержимое страницы по указанному URL.

    Args:
        url: Ссылка на страницу аниме на shikimori.one.

    Returns:
        Строка с HTML-кодом страницы.

    Raises:
        requests.HTTPError: В случае неуспешного HTTP-ответа.
        requests.RequestException: При сетевых ошибках.
    """
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def clean_text(s: str) -> str:
    """
    Очищает текст: нормализует пробелы, удаляет неразрывные пробелы.

    Args:
        s: Исходная строка.

    Returns:
        Очищенная строка.
    """
    # normalize spaces, quotes and dashes
    s = s.replace('\xa0', ' ').strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    Извлекает заголовок аниме со страницы.

    Пытается последовательно:
    1) <header> h1
    2) Микроразметка meta[itemprop="name"/"headline"]
    3) <title>

    Args:
        soup: Объект BeautifulSoup для HTML документа.

    Returns:
        Строка с названием или None, если не найдено.
    """
    # 1) header h1
    h = soup.select_one("header.head h1, header .head h1, header h1")
    if h:
        # The <h1> on Shikimori often has quotes and separators inside spans
        t = clean_text(h.get_text(" ", strip=True))
        # remove redundant quotes duplicates like: "Кэйон!" " K-On!"
        t = t.strip(' "\'')
        return t

    # 2) microdata
    m = soup.select_one('meta[itemprop="name"], meta[itemprop="headline"]')
    if m and m.get("content"):
        return clean_text(m["content"])

    # 3) <title>
    if soup.title and soup.title.string:
        return clean_text(soup.title.string.split(" / ")[0])
    return None


def extract_info_block(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Parse the left "Информация" block.
    """
    info: Dict[str, str] = {}

    containers = soup.select("div.c-about div.b-entry-info div.line-container")
    if not containers:
        # fallback: sometimes without the outer classes
        containers = soup.select("div.b-entry-info div.line-container")

    for cont in containers:
        lines = cont.select("div.line")
        if not lines:
            # sometimes <div class="line-container"><div class="line">Тип:</div><div class="value">TV Сериал</div></div>
            name = cont.select_one(".line, .name, .key")
            value = cont.select_one(".value, .val")
            if name and value:
                k = clean_text(name.get_text(" ", strip=True).rstrip(":"))
                v = clean_text(value.get_text(" ", strip=True))
                if k:
                    info[k] = v
            continue

        # happy path: first .line is key, the rest joined as value
        key = clean_text(lines[0].get_text(" ", strip=True).rstrip(":"))
        val = clean_text(" ".join([ln.get_text(" ", strip=True) for ln in lines[1:]]))
        if key:
            info[key] = val
    return info


def extract_rating(soup: BeautifulSoup) -> Optional[str]:
    """
    Извлекает числовой рейтинг аниме.

    Сначала пытается взять из микроразметки ratingValue, затем ищет
    видимое числовое значение в правом блоке страницы.

    Args:
        soup: Объект BeautifulSoup для HTML документа.

    Returns:
        Рейтинг в виде строки (например, "8.12") или None.
    """
    # Try microdata
    m = soup.select_one('meta[itemprop="ratingValue"]')
    if m and m.get("content"):
        return clean_text(m["content"])

    right = soup.select_one("div.c-about")
    text = ""
    if right:
        text = right.get_text(" ", strip=True)
    else:
        text = soup.get_text(" ", strip=True)

    mnum = re.search(r"\b(\d{1,2}[.,]\d{1,2})\b", text)
    if mnum:
        return mnum.group(1).replace(",", ".")

    return None


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    """
    Извлекает описание аниме.

    Пытается получить текст из блока текущего описания или из элемента
    с itemprop="description". Текст нормализуется.

    Args:
        soup: Объект BeautifulSoup для HTML документа.

    Returns:
        Строка с описанием или None.
    """
    node = soup.select_one("div.c-description div.description-current")
    if node:
        # Description paragraphs may contain <br> and links to characters; keep text only
        desc = clean_text(node.get_text(" ", strip=True))
        if desc:
            return desc

    node = soup.select_one('div[itemprop="description"], [itemprop="description"]')
    if node:
        desc = clean_text(node.get_text(" ", strip=True))
        if desc:
            return desc

    return None


def parse(url: str) -> Dict[str, Any]:
    """
    Парсит страницу аниме и возвращает структурированные данные.

    Args:
        url: Ссылка на страницу аниме.

    Returns:
        Словарь формата:
        {
          "<Название>": {
            "url": str,
            "info": Dict[str, str],
            "rating": Optional[str],
            "description": Optional[str]
          }
        }
    """
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    title = extract_title(soup) or "Unknown Title"
    info = extract_info_block(soup)
    rating = extract_rating(soup)
    description = extract_description(soup)

    payload: Dict[str, Any] = {
        title: {
            "url": url,
            "info": info,
            "rating": rating,
            "description": description,
        }
    }
    return payload


def main():
    """
    Точка входа CLI: парсит указанную страницу аниме и выводит JSON.

    Аргументы:
        url (позиционный): URL страницы аниме на shikimori.one
        -o / --output: Путь для сохранения результата в файл
        --ensure-ascii: Экранировать не-ASCII символы в JSON
    """
    ap = argparse.ArgumentParser(description="Parse a Shikimori anime page into JSON.")
    ap.add_argument("url", help="URL of the anime page on shikimori.one")
    ap.add_argument("-o", "--output", help="Path to save JSON file", default=None)
    ap.add_argument("--ensure-ascii", action="store_true",
                    help="Escape non-ASCII in JSON (default: keep UTF-8)")
    args = ap.parse_args()

    data = parse(args.url)

    js = json.dumps(data, ensure_ascii=args.ensure_ascii, indent=2)
    print(js)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(js)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        sys.stderr.write(f"HTTP error: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(2)

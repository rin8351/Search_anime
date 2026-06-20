#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shikimori anime page parser.

Usage:

python shikimori_parser.py https://shikimori.one/animes/5680-k-on -o k_on.json

Extracts:
- Title (from <header> <h1> or meta[itemprop="name"/"headline"])
- Info block (from div.c-about -> div.b-entry-info -> div.line-container)
- Rating (meta[itemprop="ratingValue"], then visible score near "РЕЙТИНГ")
- Description (from div.c-description > div.description-current OR div[itemprop="description"])
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
    Fetch HTML content from the given URL.

    Args:
        url: Link to an anime page on shikimori.one.

    Returns:
        HTML string.

    Raises:
        requests.HTTPError: On unsuccessful HTTP response.
        requests.RequestException: On network errors.
    """
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def clean_text(s: str) -> str:
    """
    Clean text: normalize whitespace, remove non-breaking spaces.

    Args:
        s: Input string.

    Returns:
        Cleaned string.
    """
    s = s.replace('\xa0', ' ').strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract anime title from the page.

    Tries in order:
    1) <header> h1
    2) Microdata meta[itemprop="name"/"headline"]
    3) <title>

    Args:
        soup: BeautifulSoup object for the HTML document.

    Returns:
        Title string or None if not found.
    """
    h = soup.select_one("header.head h1, header .head h1, header h1")
    if h:
        t = clean_text(h.get_text(" ", strip=True))
        t = t.strip(' "\'')
        return t

    m = soup.select_one('meta[itemprop="name"], meta[itemprop="headline"]')
    if m and m.get("content"):
        return clean_text(m["content"])

    if soup.title and soup.title.string:
        return clean_text(soup.title.string.split(" / ")[0])
    return None


def extract_info_block(soup: BeautifulSoup) -> Dict[str, str]:
    """Parse the left "Информация" (Info) block."""
    info: Dict[str, str] = {}

    containers = soup.select("div.c-about div.b-entry-info div.line-container")
    if not containers:
        containers = soup.select("div.b-entry-info div.line-container")

    for cont in containers:
        lines = cont.select("div.line")
        if not lines:
            name = cont.select_one(".line, .name, .key")
            value = cont.select_one(".value, .val")
            if name and value:
                k = clean_text(name.get_text(" ", strip=True).rstrip(":"))
                v = clean_text(value.get_text(" ", strip=True))
                if k:
                    info[k] = v
            continue

        key = clean_text(lines[0].get_text(" ", strip=True).rstrip(":"))
        val = clean_text(" ".join([ln.get_text(" ", strip=True) for ln in lines[1:]]))
        if key:
            info[key] = val
    return info


def extract_rating(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract numeric anime rating.

    Tries microdata ratingValue first, then visible numeric value
    in the right block of the page.

    Args:
        soup: BeautifulSoup object for the HTML document.

    Returns:
        Rating as string (e.g. "8.12") or None.
    """
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
    Extract anime description.

    Tries the current description block or itemprop="description".
    Text is normalized.

    Args:
        soup: BeautifulSoup object for the HTML document.

    Returns:
        Description string or None.
    """
    node = soup.select_one("div.c-description div.description-current")
    if node:
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
    Parse an anime page and return structured data.

    Args:
        url: Link to the anime page.

    Returns:
        Dictionary in the format:
        {
          "<Title>": {
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
    CLI entry point: parse the given anime page and output JSON.

    Args:
        url (positional): URL of anime page on shikimori.one
        -o / --output: path to save result to file
        --ensure-ascii: escape non-ASCII characters in JSON
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

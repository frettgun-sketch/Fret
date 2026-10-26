#!/usr/bin/env python3
import html
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path


FEEDS = [
    ("Son Dakika", "Türkiye son dakika haberleri"),
    ("Türkiye", "Türkiye gündem haberleri"),
    ("Siyaset", "Türkiye siyaset haberleri"),
    ("Spor", "Türkiye spor haberleri"),
    ("Futbol", "Türkiye futbol haberleri"),
    ("Teknoloji", "Türkiye teknoloji (site:shiftdelete.net OR site:webtekno.com OR site:donanimhaber.com)"),
    ("Ekonomi", "Türkiye ekonomi (site:bloomberght.com OR site:ntv.com.tr OR site:trthaber.com)"),
    ("Dünya", "dünya haberleri (site:bbc.com/turkce OR site:trthaber.com OR site:ntv.com.tr)"),
]
OUTPUT = Path(__file__).resolve().parent.parent / "news.json"


class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.image = ""

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img" and not self.image:
            self.image = dict(attrs).get("src", "")


def local_name(tag):
    return tag.rsplit("}", 1)[-1].split(":")[-1].lower()


def child_text(element, name):
    for child in element:
        if local_name(child.tag) == name:
            return "".join(child.itertext()).strip()
    return ""


def story_image(item, description):
    for element in item.iter():
        if local_name(element.tag) in {"content", "thumbnail", "enclosure"}:
            image = element.attrib.get("url") or element.attrib.get("href")
            if image and image.startswith(("https://", "http://")):
                return image
    parser = DescriptionParser()
    parser.feed(description)
    image = html.unescape(parser.image)
    return image if image.startswith(("https://", "http://")) else ""


def normalize_date(value):
    if not value:
        return ""
    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return date.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError):
        return ""


def parse_feed(xml_data, category):
    root = ET.fromstring(xml_data)
    stories = []
    for item in root.iter():
        if local_name(item.tag) != "item":
            continue
        title = child_text(item, "title")
        source = child_text(item, "source")
        if not source and " - " in title:
            title, source = title.rsplit(" - ", 1)
            title, source = title.strip(), source.strip()
        link = child_text(item, "link")
        description = child_text(item, "description")
        description_parser = DescriptionParser()
        description_parser.feed(description)
        description_text = re.sub(r"\s+", " ", " ".join(description_parser.parts)).strip()
        if title and link.startswith(("https://", "http://")):
            stories.append({
                "title": title.strip(),
                "link": link.strip(),
                "source": source.strip() or "Google Haberler RSS",
                "date": normalize_date(child_text(item, "pubdate")),
                "description": description_text or title.strip(),
                "image": story_image(item, description),
                "category": category,
            })
    return stories


def fetch_feed(category, query):
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "tr",
        "gl": "TR",
        "ceid": "TR:tr",
    })
    url = f"https://news.google.com/rss/search?{params}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GUNDO360-RSS-Update/1.0"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return parse_feed(response.read(), category)


def save_news(stories):
    payload = {
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stories": stories,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=OUTPUT.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, OUTPUT)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def main():
    all_stories = []
    failures = []
    for category, query in FEEDS:
        try:
            stories = fetch_feed(category, query)
            all_stories.extend(stories)
            print(f"{category}: {len(stories)} haber")
        except Exception as error:
            failures.append(category)
            print(f"{category}: RSS isteği başarısız: {error}", file=sys.stderr)

    if not all_stories:
        print("Hiç haber alınamadı; mevcut news.json korunuyor.", file=sys.stderr)
        return 1

    save_news(all_stories)
    print(f"{len(all_stories)} haber news.json dosyasına yazıldı.")
    if failures:
        print("Başarısız akışlar: " + ", ".join(failures), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

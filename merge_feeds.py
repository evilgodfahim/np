import feedparser
import hashlib
import os
from feedgen.feed import FeedGenerator
import xml.etree.ElementTree as ET

FEEDS = [
    "https://politepol.com/fd/BaUjoEn6s1Rx.xml",
    "https://politepol.com/fd/cjcFELwr80sj.xml",
]

OUTPUT_FILE = "combined.xml"
INDEX_FILE = "index.txt"
MAX_ITEMS = 200

def get_id(entry):
    if "id" in entry:
        return entry.id
    elif "link" in entry:
        return entry.link
    else:
        return hashlib.sha256(entry.title.encode("utf-8")).hexdigest()

def load_seen():
    if not os.path.exists(INDEX_FILE):
        return set()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip() and not line.startswith("#"))

def save_seen(seen):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        for item in seen:
            f.write(item + "\n")

def load_existing_entries():
    if not os.path.exists(OUTPUT_FILE):
        return {}
    tree = ET.parse(OUTPUT_FILE)
    root = tree.getroot()
    entries = {}
    for item in root.findall("./channel/item"):
        link = item.find("link").text if item.find("link") is not None else None
        title = item.find("title").text if item.find("title") is not None else ""
        eid = link or hashlib.sha256(title.encode("utf-8")).hexdigest()
        entries[eid] = {
            "title": title,
            "link": link,
            "pubDate": item.find("pubDate").text if item.find("pubDate") is not None else None,
            "description": item.find("description").text if item.find("description") is not None else None
        }
    return entries

def main():
    fg = FeedGenerator()
    fg.title("Merged RSS Feed (2 sources)")
    fg.link(href="https://yourusername.github.io/rss-merged-feed/combined.xml", rel="self")
    fg.description("Combined feed from 2 sources without duplicates")
    fg.language("en")

    seen = load_seen()
    new_seen = set(seen)

    all_entries = load_existing_entries()

    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            eid = get_id(entry)
            if eid not in seen:
                all_entries[eid] = {
                    "title": entry.title,
                    "link": entry.link if "link" in entry else None,
                    "pubDate": entry.published if "published" in entry else None,
                    "description": entry.summary if "summary" in entry else None
                }
                new_seen.add(eid)

    sorted_entries = list(all_entries.items())
    sorted_entries.sort(key=lambda x: x[1]["pubDate"] if x[1]["pubDate"] else "", reverse=True)

    for eid, data in sorted_entries[:MAX_ITEMS]:
        fe = fg.add_entry()
        fe.id(eid)
        fe.title(data["title"])
        if data["link"]:
            fe.link(href=data["link"])
        if data["pubDate"]:
            fe.pubDate(data["pubDate"])
        if data["description"]:
            fe.description(data["description"])

    fg.rss_file(OUTPUT_FILE)
    save_seen(new_seen)

if __name__ == "__main__":
    main()

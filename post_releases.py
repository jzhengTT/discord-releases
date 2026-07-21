#!/usr/bin/env python3
"""Post new releases from the Planet Tenstorrent Atom feed to a Discord channel.

Fetches the releases feed, compares entry IDs against state/seen.json, and
posts each unseen release to the Discord webhook given by DISCORD_WEBHOOK_URL.
State is rewritten after every successful post so an interrupted run never
causes duplicates.
"""

import html
import io
import json
import os
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

import feedparser
import requests

FEED_URL = "https://docs.tenstorrent.com/tt-awesome/feeds/releases.xml"
STATE_FILE = Path(__file__).parent / "state" / "seen.json"
DESCRIPTION_LIMIT = 1500
SECONDS_BETWEEN_POSTS = 1.2  # webhook limit is ~30 requests/min
REQUEST_TIMEOUT = 30
MAX_429_RETRIES = 5


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._out = io.StringIO()

    def handle_data(self, data):
        self._out.write(data)

    def text(self):
        return self._out.getvalue()


def strip_html(fragment: str) -> str:
    parser = _TextExtractor()
    parser.feed(fragment)
    return html.unescape(parser.text()).strip()


def load_seen() -> set:
    if not STATE_FILE.exists():
        return set()
    with STATE_FILE.open() as f:
        return set(json.load(f)["seen"])


def save_seen(seen: set) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    with STATE_FILE.open("w") as f:
        json.dump({"seen": sorted(seen)}, f, indent=2)
        f.write("\n")


def fetch_entries():
    resp = requests.get(FEED_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    if feed.bozo:
        sys.exit(f"error: feed failed to parse: {feed.bozo_exception}")
    if not feed.entries:
        sys.exit("error: feed parsed but contains no entries")
    return feed.entries


def build_embed(entry) -> dict:
    description = strip_html(entry.get("summary", ""))
    if len(description) > DESCRIPTION_LIMIT:
        description = description[: DESCRIPTION_LIMIT - 1].rstrip() + "…"
    embed = {
        "title": entry.title[:256],
        "url": entry.link,
        "description": description,
        "footer": {"text": "Planet Tenstorrent"},
    }
    if entry.get("updated_parsed"):
        embed["timestamp"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", entry.updated_parsed
        )
    return embed


def post_to_discord(webhook_url: str, embed: dict) -> None:
    for _ in range(MAX_429_RETRIES):
        resp = requests.post(
            webhook_url, json={"embeds": [embed]}, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 429:
            delay = float(resp.headers.get("Retry-After", "5"))
            time.sleep(delay)
            continue
        resp.raise_for_status()
        return
    sys.exit("error: still rate-limited after retries, giving up")


def main() -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        sys.exit(
            "error: DISCORD_WEBHOOK_URL is not set "
            "(create a webhook on the #releases channel and export its URL)"
        )

    entries = fetch_entries()
    seen = load_seen()
    new_entries = [e for e in entries if e.id not in seen]
    new_entries.sort(key=lambda e: e.get("updated_parsed") or time.gmtime(0))

    for entry in new_entries:
        post_to_discord(webhook_url, build_embed(entry))
        seen.add(entry.id)
        save_seen(seen)
        print(f"posted: {entry.title}")
        time.sleep(SECONDS_BETWEEN_POSTS)

    print(
        f"posted {len(new_entries)} new release(s), "
        f"skipped {len(entries) - len(new_entries)} already seen"
    )


if __name__ == "__main__":
    main()

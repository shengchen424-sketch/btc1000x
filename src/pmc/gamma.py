"""Public Gamma / CLOB reads with retries and an optional on-disk cache."""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"


def get_json(url: str, params: dict | None = None, retries: int = 4, timeout: int = 30):
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except (requests.RequestException, ValueError):
            pass
        if attempt < retries:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"GET failed after retries: {url} {params}")


def event_by_slug(slug: str, cache_dir: Path | None = None) -> dict | None:
    if cache_dir is not None:
        p = cache_dir / f"{slug}.json"
        if p.exists():
            return json.loads(p.read_text()) or None
    res = get_json(f"{GAMMA}/events", {"slug": slug})
    ev = res[0] if res else None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{slug}.json").write_text(json.dumps(ev or {}))
    return ev


def active_events(tag_slug: str, page: int = 500) -> list[dict]:
    out, offset = [], 0
    while True:
        res = get_json(f"{GAMMA}/events", {"tag_slug": tag_slug, "active": "true", "closed": "false",
                                           "limit": page, "offset": offset})
        if not res:
            break
        out.extend(res)
        if len(res) < page:
            break
        offset += page
    return out


def book(token_id: str) -> dict | None:
    return get_json(f"{CLOB}/book", {"token_id": token_id}, retries=2, timeout=15)

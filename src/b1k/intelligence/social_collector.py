"""Forward collector for public social / sentiment signals (no login, no bypassing of access controls).

Sources that work without credentials and are used here:
  - Telegram public channel previews (https://t.me/s/<channel>): the latest ~20 messages per page.
    Only channels that are public are read; the page is what any browser sees.
  - alternative.me Fear & Greed daily value.
Sources that are NOT used: X/Twitter (no free history; API is paid), Reddit (blocks this egress),
Google Trends / GDELT / Wikipedia pageviews (rate-limited from shared addresses; retried nightly).

Output: state/social/messages.jsonl (deduplicated by channel + message id), state/social/daily.jsonl
(one line per run: message counts per channel, lexicon sentiment score, F&G). Historical depth builds
up only from the day the collector starts; nothing here can be backtested before that.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import requests

from b1k.config import PATHS

STATE = PATHS.state / "social"
UA = {"User-Agent": "Mozilla/5.0 (research collector; contact via github shengchen424-sketch/btc1000x)"}
DEFAULT_CHANNELS = ["whalealertio", "cointelegraph", "binance_announcements", "bitcoin"]
BULL = ["pump", "bullish", "breakout", "ath", "all-time high", "rally", "moon", "buy", "long", "accumulate",
        "surge", "soar", "recover"]
BEAR = ["dump", "bearish", "crash", "liquidat", "sell-off", "selloff", "plunge", "short", "fear", "capitulat",
        "hack", "exploit", "ban", "lawsuit", "drop", "fall"]

MSG_RE = re.compile(r'data-post="([^"]+)".*?tgme_widget_message_text[^>]*>(.*?)</div>.*?<time datetime="([^"]+)"', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def fetch_channel(channel: str) -> list[dict]:
    r = requests.get(f"https://t.me/s/{channel}", headers=UA, timeout=20)
    if r.status_code != 200:
        return []
    out = []
    for post, html, ts in MSG_RE.findall(r.text):
        text = unescape(TAG_RE.sub(" ", html)).strip()
        text = re.sub(r"\s+", " ", text)
        out.append({"channel": channel, "id": post, "ts": ts, "text": text[:2000]})
    return out


def lexicon_score(text: str) -> int:
    t = text.lower()
    return sum(w in t for w in BULL) - sum(w in t for w in BEAR)


def fear_greed() -> int | None:
    try:
        j = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=15).json()
        return int(j["data"][0]["value"])
    except Exception:
        return None


def run_once(channels: list[str] | None = None) -> dict:
    STATE.mkdir(parents=True, exist_ok=True)
    channels = channels or DEFAULT_CHANNELS
    seen_p = STATE / "seen.json"
    seen = set(json.loads(seen_p.read_text())) if seen_p.exists() else set()
    new, per_channel, scores = [], {}, []
    for ch in channels:
        msgs = fetch_channel(ch)
        per_channel[ch] = len(msgs)
        for m in msgs:
            key = f"{m['channel']}|{m['id']}"
            if key in seen:
                continue
            seen.add(key)
            m["score"] = lexicon_score(m["text"])
            m["collected_at"] = datetime.now(timezone.utc).isoformat()
            new.append(m)
            scores.append(m["score"])
        time.sleep(1.0)  # polite
    if new:
        with open(STATE / "messages.jsonl", "a") as f:
            for m in new:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
    seen_p.write_text(json.dumps(sorted(seen)[-20000:]))
    summary = {"at": datetime.now(timezone.utc).isoformat(), "new_messages": len(new), "per_channel": per_channel,
               "mean_score_new": (sum(scores) / len(scores)) if scores else None, "fear_greed": fear_greed()}
    with open(STATE / "daily.jsonl", "a") as f:
        f.write(json.dumps(summary) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(run_once(), ensure_ascii=False))

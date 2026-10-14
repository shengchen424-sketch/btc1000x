"""Operational health: data freshness, shadow runner liveness, kill switch. Structured JSON out."""
from __future__ import annotations

import json
import time
from pathlib import Path

from b1k.config import PATHS
from b1k.risk.engine import kill_switch_engaged


def status() -> dict:
    out = {"at_ms": int(time.time() * 1000), "kill_switch": kill_switch_engaged()}
    lr = PATHS.state / "shadow" / "last_run.json"
    if lr.exists():
        j = json.loads(lr.read_text())
        out["shadow_last_run"] = j
        out["shadow_data_age_s"] = (out["at_ms"] - j["last_15m_close"]) / 1000
    else:
        out["shadow_last_run"] = None
    intents = PATHS.state / "shadow" / "intents.jsonl"
    out["shadow_intents"] = sum(1 for _ in open(intents)) if intents.exists() else 0
    return out


if __name__ == "__main__":
    print(json.dumps(status(), indent=1))

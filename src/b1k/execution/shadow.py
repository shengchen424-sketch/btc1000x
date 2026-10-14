"""Forward shadow runner: fetch closed Bitget bars, run the registered trials through the same
strategy and risk code as the backtest, persist every intent and decision BEFORE the outcome exists.
No order is sent. Run from a systemd timer every 15 minutes (ops/b1k-shadow.timer).

State: state/shadow/intents.jsonl (one line per intent, with the risk decision), state/shadow/last_run.json.
Outcomes are sealed later by `python -m b1k.execution.shadow mature` which prices each intent with
the backtester rules on Bitget 1m bars fetched after the fact.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone

import pandas as pd

from b1k.config import PATHS, RISK
from b1k.execution import bitget_public as bg
from b1k.risk import engine as risk
from b1k.strategies import REGISTRY
from b1k.strategies.base import MarketState

STATE = PATHS.state / "shadow"


def load_trials() -> list[dict]:
    p = PATHS.root / "research" / "strategy_registry" / "shadow_trials.json"
    return json.loads(p.read_text()) if p.exists() else []


def load_daily_rules() -> list[dict]:
    p = PATHS.root / "research" / "strategy_registry" / "shadow_daily_rules.json"
    return json.loads(p.read_text()) if p.exists() else []


def run_daily() -> dict:
    """Position-based daily rules (EXP-004 LEADs): after each 00:00 UTC close, compute the target
    position from Bitget's own closed daily candles and append it with a timestamp, so the forward
    record exists before the day's outcome. Idempotent per (rule, close_time)."""
    from b1k.strategies.daily_trend import RULES
    STATE.mkdir(parents=True, exist_ok=True)
    rules = load_daily_rules()
    if not rules:
        return {"daily_rules": 0}
    d = bg.candles_deep("BTCUSDT", "1d", 400)
    if len(d) < 260:
        return {"daily_rules": len(rules), "error": f"only {len(d)} daily bars from Bitget"}
    ct = int(d["close_time"].iloc[-1])
    seen_p = STATE / "daily_seen.json"
    seen = set(json.loads(seen_p.read_text())) if seen_p.exists() else set()
    n = 0
    now_ms = int(time.time() * 1000)
    for r in rules:
        key = f"{r['rule']}|{ct}"
        if key in seen:
            continue
        pos = float(RULES[r["rule"]](d).iloc[-1])
        rec = {"recorded_at_ms": now_ms, "rule": r["rule"], "status": r["status"], "close_time": ct,
               "close": float(d["close"].iloc[-1]), "target_position": pos, "mode": "DRY_RUN"}
        with open(STATE / "daily_positions.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        seen.add(key)
        n += 1
    seen_p.write_text(json.dumps(sorted(seen)[-2000:]))
    return {"daily_rules": len(rules), "new_records": n, "last_close_time": ct}


def run_once() -> dict:
    STATE.mkdir(parents=True, exist_ok=True)
    now_ms = int(time.time() * 1000)
    trials = load_trials()
    daily = run_daily()
    if not trials:
        summary = {"at": datetime.now(timezone.utc).isoformat(), "intents": 0, "trials": 0, "daily": daily,
                   "note": "no intent trials registered for shadow"}
        (STATE / "last_run.json").write_text(json.dumps(summary))
        return summary
    bars = {r: bg.candles("BTCUSDT", r) for r in {"15m", "1h", "4h"}}
    t = bg.ticker("BTCUSDT")
    rate, nf = bg.next_funding("BTCUSDT")
    seen = set()
    p_seen = STATE / "seen.json"
    if p_seen.exists():
        seen = set(json.loads(p_seen.read_text()))
    n_int = 0
    for tr in trials:
        cls = REGISTRY[tr["strategy"]]
        strat = cls(**tr["params"])
        b = bars[strat.timeframe]
        htf = bars[strat.htf] if strat.htf else None
        state = MarketState(bars=b, htf_bars=htf, as_of_ms=now_ms)
        data_age = (now_ms - int(b["close_time"].iloc[-1])) / 1000
        intent = strat.generate_signal(state)
        if intent is None:
            continue
        key = f"{strat.trial_id}|{intent.signal_timestamp}"
        if key in seen:
            continue
        seen.add(key)
        acct = risk.AccountState(equity=RISK.INITIAL_EQUITY, open_positions=0, pending_orders=0,
                                 realized_pnl_today=0.0, realized_pnl_week=0.0,
                                 mark_price=float(t["markPrice"]), best_bid=float(t["bidPr"]),
                                 best_ask=float(t["askPr"]), data_age_s=data_age, exchange_ok=True,
                                 now_ms=now_ms, next_funding_ms=nf, next_funding_rate=rate)
        dec = risk.evaluate(intent, acct)
        rec = {"recorded_at_ms": now_ms, "trial_id": strat.trial_id, "intent": intent.to_dict(),
               "decision": {"executable": dec.executable, "reasons": dec.reasons, "mode": dec.mode,
                            "plan": dec.plan.__dict__ if dec.plan else None},
               "mark_price": acct.mark_price, "data_age_s": data_age}
        if rec["decision"]["plan"]:
            rec["decision"]["plan"]["direction"] = rec["decision"]["plan"]["direction"].value
        with open(STATE / "intents.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        n_int += 1
    p_seen.write_text(json.dumps(sorted(seen)[-5000:]))
    summary = {"at": datetime.now(timezone.utc).isoformat(), "intents": n_int, "trials": len(trials),
               "last_15m_close": int(bars["15m"]["close_time"].iloc[-1]), "mark": float(t["markPrice"]),
               "daily": daily}
    (STATE / "last_run.json").write_text(json.dumps(summary))
    return summary


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        print(json.dumps(run_once()))
    else:
        print("unknown command", cmd)
        sys.exit(2)

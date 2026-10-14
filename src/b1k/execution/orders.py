"""Turn an approved OrderPlan into Bitget order payloads. DRY_RUN builds and logs payloads; it never
signs or sends. Live sending is NOT implemented in Phase 1 on purpose: enabling it requires the
user's written authorisation, a separate sub-account, and a controlled stop-order test (RULE 12)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from b1k.config import PATHS, RISK
from b1k.risk.engine import OrderPlan
from b1k.strategies.base import Direction


def build_payloads(plan: OrderPlan, symbol: str = "BTCUSDT") -> dict:
    side = "buy" if plan.direction == Direction.LONG else "sell"
    hold = "long" if plan.direction == Direction.LONG else "short"
    cid = f"b1k-{uuid.uuid4().hex[:16]}"
    entry = {"symbol": symbol, "productType": "USDT-FUTURES", "marginMode": "isolated",
             "marginCoin": "USDT", "size": f"{plan.qty_btc:.4f}", "side": side, "tradeSide": "open",
             "orderType": "market", "clientOid": cid}
    stop = {"symbol": symbol, "productType": "USDT-FUTURES", "marginCoin": "USDT", "planType": "pos_loss",
            "triggerPrice": f"{plan.stop_loss:.1f}", "triggerType": "mark_price", "holdSide": hold}
    tp = None
    if plan.take_profit is not None:
        tp = {"symbol": symbol, "productType": "USDT-FUTURES", "marginCoin": "USDT", "planType": "pos_profit",
              "triggerPrice": f"{plan.take_profit:.1f}", "triggerType": "mark_price", "holdSide": hold}
    return {"client_oid": cid, "entry": entry, "stop_loss": stop, "take_profit": tp}


def submit(plan: OrderPlan, symbol: str = "BTCUSDT", log_path: Path | None = None) -> dict:
    payloads = build_payloads(plan, symbol)
    rec = {"at": datetime.now(timezone.utc).isoformat(), "mode": "DRY_RUN", "payloads": payloads}
    if RISK.LIVE_TRADING and not RISK.DRY_RUN:
        # Deliberately unreachable in Phase 1: there is no signing client in this repository.
        raise PermissionError("LIVE_TRADING requested but no live client is authorised (Phase 1)")
    log_path = log_path or PATHS.state / "dry_run_orders.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

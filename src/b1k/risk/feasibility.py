"""10 USDT feasibility calculator for BTCUSDT perpetual on Bitget.

Inputs come only from saved exchange metadata (evidence/*.json); nothing is guessed.
Isolated-margin liquidation is approximated as: margin + unrealised loss <= maintenance
margin + closing fee, i.e. adverse move d_liq = 1/L - mmr - taker.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

LEVERAGES = (5, 10, 20, 30, 50, 75, 100)


@dataclass(frozen=True)
class Spec:
    price: float
    min_qty: float
    qty_step: float
    min_notional: float
    taker: float
    maker: float
    max_lever: int
    tier1_mmr: float
    tier1_end_usdt: float
    funding_interval_h: int

    @classmethod
    def from_evidence(cls, ev: Path) -> "Spec":
        c = json.loads((ev / "contract_BTCUSDT.json").read_text())["data"][0]
        t = json.loads((ev / "ticker_BTCUSDT.json").read_text())["data"][0]
        tiers = json.loads((ev / "position_tiers_BTCUSDT.json").read_text())["data"]
        tier1 = min(tiers, key=lambda r: int(r["level"]))
        return cls(
            price=float(t["markPrice"]),
            min_qty=float(c["minTradeNum"]),
            qty_step=float(c["sizeMultiplier"]),
            min_notional=float(c["minTradeUSDT"]),
            taker=float(c["takerFeeRate"]),
            maker=float(c["makerFeeRate"]),
            max_lever=int(c["maxLever"]),
            tier1_mmr=float(tier1["keepMarginRate"]),
            tier1_end_usdt=float(tier1["endUnit"]),
            funding_interval_h=int(c["fundInterval"]),
        )


@dataclass(frozen=True)
class Assumptions:
    equity: float = 10.0
    risk_per_trade: float = 0.01
    slip_entry: float = 0.0003      # 3 bps market entry
    slip_stop: float = 0.0010       # 10 bps on a triggered stop (market exit through the book)
    liq_buffer: float = 2.0         # liquidation distance must be >= 2x the stop distance
    funding_per_8h: float = 0.0001  # cap of the observed range, paid by longs
    hold_hours: float = 24.0


def min_position_qty(s: Spec) -> float:
    q = max(s.min_qty, s.min_notional / s.price)
    return math.ceil(round(q / s.qty_step, 9)) * s.qty_step


def evaluate(s: Spec, a: Assumptions, lever: int) -> dict:
    qty = min_position_qty(s)
    notional = qty * s.price
    margin = notional / lever
    open_fee = notional * s.taker
    risk_budget = a.equity * a.risk_per_trade
    # fixed cost of one stopped-out round trip, as a fraction of notional
    cost_frac = 2 * s.taker + a.slip_entry + a.slip_stop
    funding_frac = a.funding_per_8h * a.hold_hours / s.funding_interval_h
    max_stop = (risk_budget - notional * (cost_frac + funding_frac)) / notional
    liq_dist = 1.0 / lever - s.tier1_mmr - s.taker
    free_margin = a.equity - margin - open_fee
    checks = {
        "lever_allowed": lever <= s.max_lever,
        "margin_fits": free_margin > 0,
        "risk_budget_covers_costs": max_stop > 0,
        "liquidation_beyond_stop": liq_dist >= a.liq_buffer * max(max_stop, 0.0) and liq_dist > 0,
    }
    return {
        "leverage": lever,
        "qty_btc": round(qty, 8),
        "notional_usdt": round(notional, 4),
        "margin_usdt": round(margin, 4),
        "free_margin_usdt": round(free_margin, 4),
        "risk_budget_usdt": round(risk_budget, 4),
        "round_trip_cost_usdt": round(notional * (cost_frac + funding_frac), 4),
        "cost_share_of_risk": round(notional * (cost_frac + funding_frac) / risk_budget, 3),
        "max_stop_pct": round(100 * max_stop, 3),
        "max_stop_usd": round(max_stop * s.price, 1),
        "liq_distance_pct": round(100 * liq_dist, 3),
        "checks": checks,
        "feasible": all(checks.values()),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    s = Spec.from_evidence(root / "evidence" / "exchange")
    a = Assumptions()
    rows = [evaluate(s, a, L) for L in LEVERAGES]
    out = {"spec": asdict(s), "assumptions": asdict(a), "rows": rows}
    (root / "evidence" / "exchange" / "feasibility_10usdt.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["spec"]))
    for r in rows:
        print(r["leverage"], r["notional_usdt"], r["margin_usdt"], r["free_margin_usdt"],
              r["round_trip_cost_usdt"], r["cost_share_of_risk"], r["max_stop_pct"],
              r["max_stop_usd"], r["liq_distance_pct"], r["feasible"],
              [k for k, v in r["checks"].items() if not v])


if __name__ == "__main__":
    main()

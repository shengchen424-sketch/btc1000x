"""Independent, deterministic risk engine (RULE 8). Decides whether a SignalIntent is executable.

Pure functions over explicit state: no network, no clock reads. Every rejection names the rule.
Hard limits are constants from config; raising them is a user decision (RULE 12).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from b1k.config import RISK, COSTS, PATHS, RiskDefaults, CostModel
from b1k.strategies.base import SignalIntent, Direction


@dataclass(frozen=True)
class AccountState:
    equity: float
    open_positions: int
    pending_orders: int
    realized_pnl_today: float
    realized_pnl_week: float
    mark_price: float
    best_bid: float
    best_ask: float
    data_age_s: float
    exchange_ok: bool
    now_ms: int
    next_funding_ms: Optional[int] = None
    next_funding_rate: Optional[float] = None


@dataclass(frozen=True)
class OrderPlan:
    direction: Direction
    qty_btc: float
    notional_usdt: float
    leverage: int
    margin_usdt: float
    planned_loss_usdt: float
    planned_loss_frac: float
    liq_distance_frac: float
    stop_loss: float
    take_profit: Optional[float]


@dataclass
class Decision:
    executable: bool
    reasons: list[str] = field(default_factory=list)
    plan: Optional[OrderPlan] = None
    mode: str = "DRY_RUN"


def kill_switch_engaged(path: Path = PATHS.state / "KILL_SWITCH") -> bool:
    return path.exists()


def engage_kill_switch(reason: str, path: Path = PATHS.state / "KILL_SWITCH") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(reason)


def round_down_qty(q: float, step: float) -> float:
    return int(q / step + 1e-9) * step


def evaluate(intent: SignalIntent, acct: AccountState, risk: RiskDefaults = RISK,
             costs: CostModel = COSTS, kill: Optional[bool] = None) -> Decision:
    reasons: list[str] = []
    kill = kill_switch_engaged() if kill is None else kill
    if kill:
        reasons.append("KILL_SWITCH")
    if not acct.exchange_ok:
        reasons.append("EXCHANGE_UNAVAILABLE")
    if acct.data_age_s > risk.MAX_DATA_AGE_S:
        reasons.append(f"STALE_DATA:{acct.data_age_s:.0f}s")
    if acct.open_positions >= risk.MAX_CONCURRENT_POSITIONS:
        reasons.append("MAX_CONCURRENT_POSITIONS")
    if acct.pending_orders > 0:
        reasons.append("PENDING_ORDERS")
    if acct.realized_pnl_today <= -risk.DAILY_LOSS_LIMIT * acct.equity:
        reasons.append("DAILY_LOSS_LIMIT")
    if acct.realized_pnl_week <= -risk.WEEKLY_LOSS_LIMIT * acct.equity:
        reasons.append("WEEKLY_LOSS_LIMIT")
    if intent.stop_loss is None or intent.stop_loss <= 0:
        reasons.append("NO_STOP_LOSS")
        return Decision(False, reasons)
    long = intent.direction == Direction.LONG
    ref = acct.best_ask if long else acct.best_bid
    if ref <= 0 or acct.mark_price <= 0:
        reasons.append("NO_PRICE")
        return Decision(False, reasons)
    if (long and intent.stop_loss >= ref) or (not long and intent.stop_loss <= ref):
        reasons.append("STOP_ON_WRONG_SIDE")
    spread = (acct.best_ask - acct.best_bid) / acct.mark_price
    if spread > 0.0005:
        reasons.append(f"WIDE_SPREAD:{spread*1e4:.1f}bps")
    # stale signal: entry reference drifted away from the live price
    drift = abs(ref - intent.entry) / intent.entry
    if drift > 0.003:
        reasons.append(f"PRICE_DRIFT:{drift*1e4:.0f}bps")
    stop_frac = abs(ref - intent.stop_loss) / ref
    # planned loss per lot includes fees both ways and trigger slippage
    cost_frac = 2 * costs.taker_fee + costs.slip_entry + costs.slip_exit_trigger
    budget = acct.equity * risk.RISK_PER_TRADE
    per_btc_loss = ref * (stop_frac + cost_frac)
    qty = round_down_qty(budget / per_btc_loss, costs.qty_step_btc)
    if qty < costs.min_qty_btc or qty * ref < costs.min_notional_usdt:
        reasons.append(f"BELOW_MIN_ORDER:needs {per_btc_loss*costs.min_qty_btc:.4f} USDT risk, budget {budget:.4f}")
        qty = costs.min_qty_btc
    notional = qty * ref
    lever = min(risk.MAX_LEVERAGE, 150)
    margin = notional / lever
    liq = 1.0 / lever - costs.tier1_mmr - costs.taker_fee
    if liq < risk.LIQ_BUFFER_MULT * stop_frac:
        reasons.append(f"LIQUIDATION_TOO_CLOSE:{liq*100:.2f}% vs stop {stop_frac*100:.2f}%")
    if margin + notional * costs.taker_fee > acct.equity:
        reasons.append("INSUFFICIENT_MARGIN")
    planned_loss = qty * per_btc_loss
    if planned_loss > budget * 1.0001:
        reasons.append(f"PLANNED_LOSS_EXCEEDS_BUDGET:{planned_loss:.4f}>{budget:.4f}")
    if acct.next_funding_rate is not None and acct.next_funding_ms is not None:
        pays = (long and acct.next_funding_rate > 0) or (not long and acct.next_funding_rate < 0)
        if pays and abs(acct.next_funding_rate) > 0.0005 and acct.next_funding_ms - acct.now_ms < 3_600_000:
            reasons.append(f"FUNDING_EXPOSURE:{acct.next_funding_rate*1e4:.1f}bps")
    plan = OrderPlan(intent.direction, qty, notional, lever, margin, planned_loss,
                     planned_loss / acct.equity, liq, intent.stop_loss, intent.take_profit)
    mode = "LIVE" if (risk.LIVE_TRADING and not risk.DRY_RUN) else "DRY_RUN"
    return Decision(executable=not reasons, reasons=reasons, plan=plan, mode=mode)

import numpy as np
import pandas as pd

from b1k.features import ta
from b1k.risk import engine as risk, feasibility
from b1k.strategies.base import SignalIntent, Direction
from b1k.config import RISK, COSTS
from tests.conftest import make_1m


def test_prior_swing_excludes_current_bar():
    df = make_1m(200)
    psl = ta.prior_swing_low(df, 10)
    i = 150
    assert np.isclose(psl.iloc[i], df["low"].iloc[i - 10:i].min())


def test_atr_positive_and_causal():
    df = make_1m(300)
    a = ta.atr(df, 14)
    assert (a.dropna() > 0).all()
    a_short = ta.atr(df.iloc[:200], 14)
    assert np.isclose(a_short.iloc[-1], a.iloc[199])


def _intent(entry=80_000.0, stop=79_500.0, d=Direction.LONG):
    return SignalIntent("T", "1", 0, d, entry, stop, stop, None, 10)


def _acct(**kw):
    base = dict(equity=10.0, open_positions=0, pending_orders=0, realized_pnl_today=0.0,
                realized_pnl_week=0.0, mark_price=80_000.0, best_bid=79_999.9, best_ask=80_000.1,
                data_age_s=10.0, exchange_ok=True, now_ms=0)
    base.update(kw)
    return risk.AccountState(**base)


def test_risk_accepts_feasible_one_lot():
    d = risk.evaluate(_intent(), _acct(), kill=False)
    assert d.executable, d.reasons
    assert d.plan.qty_btc == COSTS.min_qty_btc
    assert d.plan.planned_loss_usdt <= RISK.RISK_PER_TRADE * 10.0 + 1e-9
    assert d.mode == "DRY_RUN"


def test_risk_rejects_each_hard_limit():
    assert "KILL_SWITCH" in risk.evaluate(_intent(), _acct(), kill=True).reasons
    assert "MAX_CONCURRENT_POSITIONS" in risk.evaluate(_intent(), _acct(open_positions=1), kill=False).reasons
    assert "DAILY_LOSS_LIMIT" in risk.evaluate(_intent(), _acct(realized_pnl_today=-0.31), kill=False).reasons
    assert "WEEKLY_LOSS_LIMIT" in risk.evaluate(_intent(), _acct(realized_pnl_week=-0.61), kill=False).reasons
    assert any(r.startswith("STALE_DATA") for r in risk.evaluate(_intent(), _acct(data_age_s=999), kill=False).reasons)
    assert "EXCHANGE_UNAVAILABLE" in risk.evaluate(_intent(), _acct(exchange_ok=False), kill=False).reasons
    assert "STOP_ON_WRONG_SIDE" in risk.evaluate(_intent(stop=80_500.0), _acct(), kill=False).reasons


def test_risk_rejects_stop_wider_than_budget():
    # 2% stop on one lot (~8 USDT) = 0.16 USDT planned loss > 0.10 budget
    d = risk.evaluate(_intent(stop=78_400.0), _acct(), kill=False)
    assert not d.executable
    assert any(r.startswith("BELOW_MIN_ORDER") or r.startswith("PLANNED_LOSS_EXCEEDS") for r in d.reasons)


def test_feasibility_table_matches_exchange_rules(tmp_path):
    s = feasibility.Spec(price=83_720.6, min_qty=0.0001, qty_step=0.0001, min_notional=5.0, taker=0.0006,
                         maker=0.0002, max_lever=150, tier1_mmr=0.004, tier1_end_usdt=200_000, funding_interval_h=8)
    a = feasibility.Assumptions()
    rows = {L: feasibility.evaluate(s, a, L) for L in feasibility.LEVERAGES}
    assert rows[10]["feasible"] and rows[30]["feasible"]
    assert not rows[50]["feasible"] and not rows[100]["feasible"]
    assert np.isclose(rows[10]["notional_usdt"], 8.3721, atol=1e-3)
    assert abs(rows[10]["liq_distance_pct"] - 9.54) < 0.01

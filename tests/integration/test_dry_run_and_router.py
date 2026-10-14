import json

import pandas as pd

from b1k.execution.orders import build_payloads, submit
from b1k.risk.engine import OrderPlan
from b1k.strategies.base import Direction
from b1k.portfolio.router import learn_eligibility, route
from b1k.learning.trade_log import classify_loss


def test_dry_run_builds_isolated_payloads_and_never_sends(tmp_path):
    plan = OrderPlan(Direction.LONG, 0.0001, 8.0, 10, 0.8, 0.09, 0.009, 0.095, 79_000.0, 81_000.0)
    p = build_payloads(plan)
    assert p["entry"]["marginMode"] == "isolated" and p["entry"]["orderType"] == "market"
    assert p["stop_loss"]["planType"] == "pos_loss" and p["take_profit"]["planType"] == "pos_profit"
    rec = submit(plan, log_path=tmp_path / "o.jsonl")
    assert rec["mode"] == "DRY_RUN"
    assert len(open(tmp_path / "o.jsonl").readlines()) == 1


def test_router_learns_on_train_and_filters():
    train = pd.DataFrame({"trial_id": ["A"] * 40 + ["A"] * 40, "regime": ["TREND_UP"] * 40 + ["RANGE"] * 40,
                          "net_r": [0.5] * 35 + [-0.5] * 5 + [-0.5] * 35 + [0.5] * 5})
    el = learn_eligibility(train)
    assert set(el[el["eligible"]]["regime"]) == {"TREND_UP"}
    val = pd.DataFrame({"trial_id": ["A", "A"], "regime": ["TREND_UP", "RANGE"], "net_r": [1, -1],
                        "signal_time": [1, 2], "exit_time": [10, 20]})
    out = route(val, el)
    assert len(out) == 1 and out["regime"].iloc[0] == "TREND_UP"


def test_loss_taxonomy_is_deterministic():
    assert classify_loss({"net_r": 0.3}) is None
    assert classify_loss({"net_r": -2.0, "exit_reason": "STOP"}) == "EXECUTION_FAILURE"
    assert classify_loss({"net_r": -1.0, "exit_reason": "STOP", "mfe_r": 0.0}) == "MODEL_FAILURE"
    assert classify_loss({"net_r": -1.0, "exit_reason": "STOP", "mfe_r": 0.8}) == "NORMAL_STATISTICAL"
    assert classify_loss({"net_r": -1.0, "regime": "RANGE", "mfe_r": 0.8}, {"TREND_UP"}) == "REGIME_MISMATCH"

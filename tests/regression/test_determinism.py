"""Two runs of the same trial on the same data must be identical."""
import hashlib

import pandas as pd

from b1k.backtest.engine import Backtester
from b1k.data.store import resample
from b1k.strategies import FailedBreak
from tests.conftest import make_1m


def _digest(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df.drop(columns=[c for c in df.columns if c.startswith("f_")]), index=False).values.tobytes()).hexdigest()


def test_rerun_is_bit_identical():
    m = make_1m(15 * 2000, seed=11, vol=0.0012)
    b = resample(m, "15m")
    s = FailedBreak(side="SHORT", lookback=20)
    t1 = Backtester(m, None).run(s, b)
    t2 = Backtester(m, None).run(FailedBreak(side="SHORT", lookback=20), b)
    assert len(t1) > 0
    assert _digest(t1) == _digest(t2)

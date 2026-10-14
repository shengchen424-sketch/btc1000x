import numpy as np
import pandas as pd
import pytest


def make_1m(n: int = 3000, start_ms: int = 1_700_000_000_000 // 60_000 * 60_000, seed: int = 1,
            vol: float = 0.0008, drift: float = 0.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(drift, vol, n)
    close = 30_000 * np.exp(np.cumsum(r))
    open_ = np.r_[close[0], close[:-1]]
    hi = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, vol / 2, n)))
    lo = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, vol / 2, n)))
    ot = start_ms + 60_000 * np.arange(n)
    return pd.DataFrame({"open_time": ot, "open": open_, "high": hi, "low": lo, "close": close,
                         "volume": rng.uniform(1, 10, n), "quote_volume": 0.0, "count": 1,
                         "taker_buy_volume": 0.0})


@pytest.fixture
def bars1m():
    return make_1m()

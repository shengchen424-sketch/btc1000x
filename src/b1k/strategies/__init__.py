from .base import SignalIntent, MarketState, Strategy, Direction  # noqa: F401
from .failed_break import FailedBreak  # noqa: F401
from .trend_pullback import TrendPullback  # noqa: F401

REGISTRY = {"FAILED_BREAK": FailedBreak, "TREND_PULLBACK": TrendPullback}

"""EXP-016b: fair-value engine calibration for Polymarket up/down windows on TRAIN, one evaluation on
VALIDATION. Registration: research/registrations/EXP-016.md. The holdout (2025+) is not loaded."""
from __future__ import annotations

import json
import subprocess
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import optimize, stats

from b1k.config import PATHS, SPLITS
from pmc import spot

if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src", "research/experiments"]).returncode:
    sys.exit("refusing to run on uncommitted code")

OUT = PATHS.results / "EXP-016"
FRACS = (0.2, 0.4, 0.6, 0.8, 0.9)
BINS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.995]
HALF_LIFE = 60
ET = ZoneInfo("America/New_York")


def reading_016a() -> str:
    txt = (OUT / "016a.md").read_text()
    return "I2" if "I2 (window average)" in txt.split("Adopted reading:")[1] else (
        "I1" if "I1 (end-point)" in txt.split("Adopted reading:")[1] else "UNRESOLVED")


def load() -> pd.DataFrame:
    end = SPLITS.validation[1]
    assert end < SPLITS.holdout[0]
    df = spot.range_1m("2019-12-31", end)[["open", "close"]]
    full = pd.date_range(df.index[0], df.index[-1], freq="1min", tz="UTC")
    df = df.reindex(full).ffill()          # archive gaps: carry the last price (counted below)
    r = np.log(df["close"]).diff().fillna(0.0)
    lam = 1 - 0.5 ** (1 / HALF_LIFE)
    df["sig"] = np.sqrt(r.pow(2).ewm(alpha=lam, adjust=False).mean()).clip(lower=1e-5)
    return df


def samples(df: pd.DataFrame, kind: str, reading: str) -> pd.DataFrame:
    """One row per (window, decision fraction): x (log distance to the barrier), scale (sd in log
    units at k = 1), up (outcome), day (UTC date of the decision, the bootstrap block)."""
    idx = df.index
    pos = pd.Series(np.arange(len(idx)), index=idx)
    op, cl, sg = df["open"].to_numpy(), df["close"].to_numpy(), df["sig"].to_numpy()
    if kind == "1d":
        noons = pd.date_range(idx[0].tz_convert(ET).normalize(), idx[-1].tz_convert(ET).normalize(), freq="D")
        noons = (noons + pd.Timedelta(hours=12)).tz_convert("UTC")
        starts = pos.reindex(noons).dropna().astype(int).to_numpy()
        W = np.diff(starts)                      # 1440 except at DST changes (1380 / 1500)
        starts = starts[:-1]
    else:
        w = {"15m": 15, "1h": 60, "4h": 240}[kind]
        starts = np.where((idx.hour * 60 + idx.minute) % w == 0)[0]
        starts = starts[starts + w < len(idx)]
        W = np.full(len(starts), w)
    rows = []
    cum = np.concatenate([[0.0], np.cumsum(cl)])
    for f in FRACS:
        m = np.round(f * W).astype(int)
        tau = W - m
        if kind == "1d":                          # close at 12:00 ET yesterday vs today
            s0, sm, se = cl[starts], cl[starts + m], cl[starts + W]
        else:                                     # open of the first bar vs close of the last
            s0, sm, se = op[starts], cl[starts + m - 1], cl[starts + W - 1]
        sig = sg[starts + m - 1]
        if reading == "I2" and kind in ("15m", "4h"):
            run_mean = (cum[starts + m] - cum[starts]) / m
            end_mean = (cum[starts + W] - cum[starts]) / W
            r_ = tau / W
            x = (1 - r_) * np.log(run_mean / s0) + r_ * np.log(sm / s0)
            scale = sig * r_ * np.sqrt(tau / 3.0)
            up = end_mean >= s0
        else:
            x = np.log(sm / s0)
            scale = sig * np.sqrt(tau)
            up = (se > s0) if kind == "1d" else (se >= s0)
            if kind == "1d":
                keep = se != s0
                x, scale, up = np.where(keep, x, np.nan), scale, up
        rows.append(pd.DataFrame({"f": f, "x": x, "scale": scale, "up": up,
                                  "day": idx[starts + m - 1].normalize()}))
    return pd.concat(rows).dropna()


def prob(x, scale, k, df_t=None):
    z = x / (k * scale)
    if df_t is None:
        return stats.norm.cdf(z)
    return stats.t.cdf(z / np.sqrt((df_t - 2) / df_t), df_t)


def logloss(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def fit(tr: pd.DataFrame) -> dict:
    x, s, y = tr.x.to_numpy(), tr.scale.to_numpy(), tr.up.to_numpy().astype(float)
    m0 = logloss(prob(x, s, 1.0), y)
    r1 = optimize.minimize_scalar(lambda k: logloss(prob(x, s, k), y), bounds=(0.3, 3.0), method="bounded")
    r2 = optimize.minimize(lambda v: logloss(prob(x, s, v[0], v[1]), y), x0=[r1.x, 6.0],
                           bounds=[(0.3, 3.0), (2.5, 50.0)], method="L-BFGS-B")
    cands = {"M0": (m0, {"k": 1.0, "df": None}), "M1": (r1.fun, {"k": float(r1.x), "df": None}),
             "M2": (float(r2.fun), {"k": float(r2.x[0]), "df": float(r2.x[1])})}
    best = min(cands, key=lambda c: cands[c][0])
    return {"train_logloss": {c: v[0] for c, v in cands.items()}, "selected": best, **cands[best][1]}


def reliability(va: pd.DataFrame, p: np.ndarray, rng) -> pd.DataFrame:
    q = np.maximum(p, 1 - p)
    hit = np.where(p >= 0.5, va.up.to_numpy(), ~va.up.to_numpy()).astype(float)
    b = np.digitize(q, BINS) - 1
    ok = (b >= 0) & (b < len(BINS) - 1)
    d = pd.DataFrame({"day": va.day.to_numpy()[ok], "bin": b[ok], "err": (hit - q)[ok], "n": 1, "q": q[ok], "hit": hit[ok]})
    per = d.groupby(["day", "bin"]).agg(err=("err", "sum"), n=("n", "sum")).unstack(fill_value=0)
    days = per.index.to_numpy()
    E, N = per["err"].to_numpy(), per["n"].to_numpy()
    boots = []
    for _ in range(1000):
        ii = rng.integers(0, len(days), len(days))
        boots.append(E[ii].sum(0) / np.maximum(N[ii].sum(0), 1))
    boots = np.array(boots)
    out = []
    for j, bi in enumerate(per["n"].columns):
        g = d[d.bin == bi]
        lo, hi = np.percentile(boots[:, j], [5, 95])
        out.append({"bin": f"[{BINS[bi]}, {BINS[bi + 1]})", "n": len(g), "mean_p": g.q.mean(),
                    "hit": g.hit.mean(), "err_pp": 100 * (g.hit.mean() - g.q.mean()),
                    "ci90_lo_pp": 100 * lo, "ci90_hi_pp": 100 * hi,
                    "ok": (len(g) < 500) or (lo <= 0.01 and hi >= -0.01)})
    return pd.DataFrame(out)


def main():
    reading = reading_016a()
    kinds = ["1h", "1d"] + (["15m", "4h"] if reading != "UNRESOLVED" else [])
    df = load()
    rng = np.random.default_rng(16)
    tr_end, va_start = pd.Timestamp(SPLITS.train[1], tz="UTC") + pd.Timedelta(days=1), pd.Timestamp(SPLITS.validation[0], tz="UTC")
    lines = ["# EXP-016b results", "", f"016a reading used for 15m/4h: {reading}. Spot 1 m, TRAIN "
             f"{SPLITS.train[0]}..{SPLITS.train[1]}, VALIDATION {SPLITS.validation[0]}..{SPLITS.validation[1]}. "
             f"Holdout not loaded.", ""]
    summary = {}
    for kind in kinds:
        s = samples(df, kind, reading)
        s = s[s.day >= pd.Timestamp(SPLITS.train[0], tz="UTC")]
        tr, va = s[s.day < tr_end], s[s.day >= va_start]
        fp = fit(tr)
        p = prob(va.x.to_numpy(), va.scale.to_numpy(), fp["k"], fp["df"])
        y = va.up.to_numpy().astype(float)
        rel = reliability(va, p, rng)
        verdict = "CALIBRATED" if rel.ok.all() else "NOT_CALIBRATED"
        p_m0 = prob(va.x.to_numpy(), va.scale.to_numpy(), 1.0)
        summary[kind] = {**fp, "n_train": len(tr), "n_val": len(va), "val_brier": float(np.mean((p - y) ** 2)),
                         "val_logloss": logloss(p, y), "val_brier_M0": float(np.mean((p_m0 - y) ** 2)),
                         "verdict": verdict}
        lines += [f"## {kind}: {verdict}", "",
                  f"Selected {fp['selected']} (k = {fp['k']:.3f}" + (f", df = {fp['df']:.1f}" if fp["df"] else "") +
                  f"); TRAIN log loss M0/M1/M2 = " + " / ".join(f"{v:.4f}" for v in fp["train_logloss"].values()) +
                  f". VALIDATION n = {len(va):,}, Brier {summary[kind]['val_brier']:.4f} (M0 {summary[kind]['val_brier_M0']:.4f}), "
                  f"log loss {summary[kind]['val_logloss']:.4f}.", "",
                  rel.to_markdown(index=False, floatfmt=".3f"), ""]
        byf = pd.DataFrame({"f": va.f.to_numpy(), "p": p, "y": y}).groupby("f").apply(
            lambda g: pd.Series({"n": len(g), "brier": np.mean((g.p - g.y) ** 2)}), include_groups=False)
        lines += ["Brier by elapsed fraction (descriptive): " + ", ".join(f"{f}: {r.brier:.4f}" for f, r in byf.iterrows()), ""]
    gaps = int(df["close"].isna().sum())
    lines += [f"Archive minutes forward-filled: see manifests; NaN after fill: {gaps}."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "016b.md").write_text("\n".join(lines) + "\n")
    (OUT / "016b_params.json").write_text(json.dumps(summary, indent=2, default=float))
    print("\n".join(lines))


if __name__ == "__main__":
    main()

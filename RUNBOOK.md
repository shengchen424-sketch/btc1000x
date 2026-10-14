# RUNBOOK

## VPS deployment (isolated; touches nothing else)

```
cd /root && git clone https://github.com/shengchen424-sketch/btc1000x && cd btc1000x
python3 -m venv .venv && . .venv/bin/activate && pip install -e .[dev]
python -m pytest
nice python -m b1k.data.binance_archive        # once; ~180 MB under data/parquet
```

Shadow runner (DRY_RUN, every 15 minutes, no orders):

```
cp ops/b1k-shadow.service ops/b1k-shadow.timer /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now b1k-shadow.timer
python -m b1k.monitoring.health
```

Only trials listed in `research/strategy_registry/shadow_trials.json` run in shadow. An empty list
means the runner records nothing (Phase 1 outcome).

## Kill switch

`touch state/KILL_SWITCH` — every risk decision becomes non-executable until the file is removed.

## Daily checks

- `python -m b1k.monitoring.health` : `shadow_data_age_s` < 1800, `kill_switch` false.
- `tail -3 state/shadow/intents.jsonl` : intents are written with the decision BEFORE outcomes exist.
- Disk: `du -sh data state` (budget: < 1 GB).

## Never

- Change `config.RiskDefaults` or `CostModel` without a new registration.
- Set `LIVE_TRADING` without the owner's written authorisation and a separate sub-account.
- Run an experiment on uncommitted code, or widen a grid under an existing experiment id.
- Read the sealed holdout except for a registered confirmation of a CANDIDATE.

"""리밸런싱 스케줄 + RSI 전술매매 규칙."""
from __future__ import annotations

import pandas as pd


def rebalance_dates(index: pd.DatetimeIndex, freq: str) -> list[pd.Timestamp]:
    idx = index.sort_values()
    if freq == "1W":
        step = 5
        return list(idx[::step])
    if freq == "2W":
        step = 10
        return list(idx[::step])
    if freq == "4W":
        step = 20
        return list(idx[::step])
    if freq == "M":
        return list(idx.to_series().groupby([idx.year, idx.month]).tail(1).sort_index().index)
    if freq == "Q":
        return list(idx.to_series().groupby([idx.year, idx.quarter]).tail(1).sort_index().index)
    raise ValueError(f"unknown freq: {freq}")


def target_weights(picks: list[str], weight_each: float, cash_weight: float) -> dict[str, float]:
    w = {t: weight_each for t in picks}
    w["CASH"] = cash_weight
    return w


def resolve_period(cfg: dict, mode: str) -> dict:
    """2단계 개발 절차용 기간 해석.
    experiment: 2023년 개발·튜닝 (설계 ≤2022-12-31, 산출물 outputs_exp).
    final: 2024~2025 본 백테스트 (config 값 그대로)."""
    if mode == "experiment":
        return {"warmup": "2022-10-01", "cutoff": "2022-12-31",
                "start": "2023-01-01", "end": "2023-12-31",
                "outdir": "outputs_exp"}
    return {"warmup": cfg.get("warmup_start", "2023-10-01"),
            "cutoff": cfg.get("design_cutoff", "2023-12-31"),
            "start": cfg["start"], "end": cfg["end"],
            "outdir": cfg["outputs"]["dir"]}

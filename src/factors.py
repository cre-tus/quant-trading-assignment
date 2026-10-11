"""과제 옵션1 팩터 랭킹: PER 오름차순 + PBR 오름차순 합산랭크.

스냅샷 시점의 EPS0/BPS0를 이용해 각 리밸런싱일의
PER_t = P_t/EPS0, PBR_t = P_t/BPS0 로 동적 랭킹을 계산한다.
(신규 정보 유입 없이 가격 변화만으로 순위 변동 → look-ahead 없음)
EPS0/BPS0가 비양수이면 해당 종목은 최하위 취급.
"""
from __future__ import annotations

import pandas as pd


def snapshot_units(fund: pd.DataFrame, price0: pd.Series) -> pd.DataFrame:
    eps = price0 / fund["trailingPE"].replace(0, float("nan"))
    bps = price0 / fund["priceToBook"].replace(0, float("nan"))
    return pd.DataFrame({"EPS0": eps, "BPS0": bps})


def rank_at(price_row: pd.Series, units: pd.DataFrame) -> pd.Series:
    per = price_row / units["EPS0"]
    pbr = price_row / units["BPS0"]
    per = per.where((units["EPS0"] > 0) & per.gt(0), float("inf"))
    pbr = pbr.where((units["BPS0"] > 0) & pbr.gt(0), float("inf"))
    score = per.rank(ascending=True) + pbr.rank(ascending=True)
    return score.sort_values()

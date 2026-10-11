"""헤드앤숄더 천장형 + 상승추세 판정 (리밸런싱 강제매도 방지용).

상승곡선 보유종목은 리밸런싱에서 팔지 않고, 천장형(H&S 완성)이 확인될 때만
내보낸다. 일봉 종가 기준 단순화 버전이다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _peaks(s: pd.Series, order: int) -> list:
    """양옆 order봉보다 큰 봉우리 인덱스 (인접 중복은 첫 번째만)."""
    v = s.values
    out = []
    for i in range(order, len(v) - order):
        if v[i] == v[i - order:i + order + 1].max() and (v[i] > v[i - 1] or v[i] > v[i + 1]):
            if out and i - out[-1] < order:
                continue
            out.append(i)
    return out


def head_and_shoulders_top(close: pd.Series, order: int = 5,
                           lookback: int = 60, tol: float = 0.05) -> bool:
    """최근 lookback봉에 H&S 천장형 + 넥라인 하향 이탈이 있으면 True."""
    s = close.dropna().iloc[-lookback:]
    if len(s) < 3 * order + 3:
        return False
    v = s.values
    peaks = _peaks(s, order)
    if len(peaks) < 3:
        return False
    i1, i2, i3 = peaks[-3], peaks[-2], peaks[-1]
    p1, p2, p3 = v[i1], v[i2], v[i3]
    if not (p2 > p1 and p2 > p3):
        return False
    if abs(p1 - p3) / p2 > tol:  # 양 어깨 대칭
        return False
    t1 = v[i1:i2 + 1].min()  # 왼쪽 골
    t2 = v[i2:i3 + 1].min()  # 오른쪽 골
    neck = t1 + (t2 - t1) * (len(v) - 1 - i1) / max(i3 - i1, 1)  # 넥라인 연장값
    return bool(v[-1] < neck)


def uptrend_intact(close: pd.Series, ma_window: int = 20) -> bool:
    """종가가 상승 중인 20일선 위에 있으면 True (상승곡선 보유)."""
    s = close.dropna()
    if len(s) < ma_window + 5:
        return False
    m = s.rolling(ma_window).mean()
    return bool(s.iloc[-1] > m.iloc[-1] and m.iloc[-1] > m.iloc[-6])


def keep_winner(close: pd.Series) -> bool:
    """강제매도 면제: 상승추세 + 천장형 없음."""
    return uptrend_intact(close) and not head_and_shoulders_top(close)

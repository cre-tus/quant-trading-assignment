"""기술지표: Wilder RSI(14 기본)."""
from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    out = 100 - 100 / (1 + rs)
    return out.fillna(50.0)  # 초기값 중립


def macd_hist(close: pd.Series, fast: int = 12, slow: int = 26,
              signal: int = 9) -> pd.Series:
    """MACD 히스토그램. 양전환=상승 모멘텀, 음전환=하락."""
    macd = close.ewm(span=fast, adjust=False).mean() \
        - close.ewm(span=slow, adjust=False).mean()
    return macd - macd.ewm(span=signal, adjust=False).mean()


def bollinger_pctb(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """%B. 0 이하=하단 이탈(과매도), 1 이상=상단 돌파(과매수)."""
    mid = close.rolling(window).mean()
    sd = close.rolling(window).std()
    return (close - (mid - num_std * sd)) / (2 * num_std * sd)


def ma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()

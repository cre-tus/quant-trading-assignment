"""필수 성능지표: PL CAGR, Buy&Hold Return, MDD + 보조지표."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _mdd(equity: pd.Series) -> tuple[float, str | None, str | None]:
    peak = equity.cummax()
    dd = equity / peak - 1
    end = dd.idxmin()
    start = equity.loc[:end].idxmax()
    return float(dd.min()), str(start.date()), str(end.date())


def strategy_metrics(equity: pd.Series) -> dict:
    equity = equity.dropna()
    if len(equity) < 2:
        raise ValueError("empty equity: 가격 데이터가 비어 백테스트를 계산할 수 없음")
    yrs = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    total_ret = float(equity.iloc[-1] / equity.iloc[0] - 1)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / yrs) - 1)
    mdd, ps, pe = _mdd(equity)
    daily = equity.pct_change().dropna()
    sharpe = float(daily.mean() / daily.std() * np.sqrt(252)) if daily.std() else 0.0
    vol = float(daily.std() * np.sqrt(252)) if len(daily) else 0.0
    return {"total_return": total_ret, "CAGR": cagr, "MDD": mdd,
            "MDD_peak": ps, "MDD_trough": pe,
            "sharpe": sharpe, "volatility": vol,
            "start": str(equity.index[0].date()), "end": str(equity.index[-1].date())}


def buy_and_hold(prices: pd.DataFrame, capital: float) -> pd.Series:
    """동일 유니버스 균등비중 buy&hold(리밸런싱 없음) 총평가액 곡선."""
    w = capital / len(prices.columns)
    shares = w / prices.iloc[0]
    return (prices * shares).sum(axis=1)


# 외부 라이브러리에서 가져다 쓰는 선별 지표 (자작 계산의 교차검증용).
# 제출 기준값은 위 자작 함수가 유지하고, 아래는 검증용으로만 기록한다.
CROSS_CHECK_METRICS = ("annual_return", "max_drawdown", "sharpe_ratio",
                       "sortino_ratio", "calmar_ratio")


def cross_check(equity: pd.Series) -> dict:
    """empyrical 선별 지표로 자작 지표를 교차검증. 실패해도 파이프라인은 계속."""
    out: dict = {"lib": "empyrical-reloaded", "metrics": CROSS_CHECK_METRICS}
    try:
        import empyrical as ep
        rets = equity.dropna().pct_change().dropna()
        fns = {"annual_return": ep.annual_return, "max_drawdown": ep.max_drawdown,
               "sharpe_ratio": ep.sharpe_ratio, "sortino_ratio": ep.sortino_ratio,
               "calmar_ratio": ep.calmar_ratio}
        out["values"] = {}
        for name in CROSS_CHECK_METRICS:  # empyrical은 전부 수익률 입력
            out["values"][name] = round(float(fns[name](rets)), 6)
        out["available"] = True
    except Exception as e:
        out["available"] = False
        out["reason"] = str(e)
    return out

"""종목별 탐색 리포트 (투자회사식 종목 손익표).

어느 종목을 얼마나 사고팔고, 실현·미실현·합계 손익이 얼마인지 한 표에 정리.
신호별 실험 폴더마다 discovery.csv로 저장해 지표별 종목 탐색에 쓴다.
"""
from __future__ import annotations

import pandas as pd

COLUMNS = ["ticker", "name_kr", "buys_n", "buys_amt", "sells_n", "sells_amt",
           "realized_pnl", "end_qty", "end_value", "end_cost",
           "unrealized_pnl", "unrealized_ret", "total_pnl"]


def _f(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return v if v == v else 0.0  # NaN → 0


def slim_daily(daily: pd.DataFrame, max_cols: int = 2000) -> pd.DataFrame:
    """대형 풀용: 전 기간 미보유 종목의 5종 컬럼 제거 (용량 폭증 방지)."""
    if daily.shape[1] <= max_cols:
        return daily
    base = {"date", "reason", "total", "cash", "total_return"}
    held = set()
    for c in daily.columns:
        if c.endswith("_qty") and (daily[c].fillna(0) != 0).any():
            held.add(c[:-4])
    keep = [c for c in daily.columns
            if c in base or c.rsplit("_", 1)[0] in held]
    return daily[keep]


def discovery_report(trades: pd.DataFrame, daily: pd.DataFrame,
                     names: dict | None = None) -> pd.DataFrame:
    from .names import name_of
    tickers = sorted({c[:-4] for c in daily.columns if c.endswith("_qty")}
                     | (set(trades["ticker"].unique()) if len(trades) else set()))
    if not tickers or not len(daily):
        return pd.DataFrame(columns=COLUMNS)
    buys = trades[trades["type"] == "BUY"] if len(trades) else trades
    sells = trades[trades["type"] == "SELL"] if len(trades) else trades
    last = daily.iloc[-1]
    rows = []
    for t in tickers:
        bt = buys[buys["ticker"] == t] if len(buys) else buys
        st = sells[sells["ticker"] == t] if len(sells) else sells
        end_qty = _f(last.get(f"{t}_qty", 0.0))
        end_val = _f(last.get(f"{t}_value", 0.0))
        end_cost = _f(last.get(f"{t}_cost", 0.0))
        realized = _f(st["pnl"].sum()) if len(st) and "pnl" in st else 0.0
        unreal = end_val - end_qty * end_cost
        rows.append({
            "ticker": t, "name_kr": name_of(t, names), "buys_n": len(bt),
            "buys_amt": round(_f(bt["amount"].sum()) if len(bt) else 0.0, 2),
            "sells_n": len(st),
            "sells_amt": round(_f(st["amount"].sum()) if len(st) else 0.0, 2),
            "realized_pnl": round(realized, 2),
            "end_qty": round(end_qty, 4), "end_value": round(end_val, 2),
            "end_cost": round(end_cost, 4),
            "unrealized_pnl": round(unreal, 2),
            "unrealized_ret": round(end_val / (end_qty * end_cost) - 1, 4)
                               if end_qty * end_cost else 0.0,
            "total_pnl": round(realized + unreal, 2),
        })
    return pd.DataFrame(rows, columns=COLUMNS).sort_values(
        "total_pnl", ascending=False).reset_index(drop=True)

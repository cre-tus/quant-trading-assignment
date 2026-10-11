"""일별 이벤트 백테스트 엔진.

포지션: 현금 + 주식 수량. 모든 주문은 종가 체결(당일 종가 기준, 분할 불가).
기록: trade_log(매 거래), snapshots(거래일별 종목 잔고/평가액/수익률 + 총계).
"""
from __future__ import annotations

import pandas as pd

from .indicators import bollinger_pctb, macd_hist, ma, rsi
from .strategies import load_strategy
from .strategy import rebalance_dates


def _avg_cost(cost: float, qty: float, spend: float, q: float) -> float:
    """매수 후 평단 (수수료 포함 실제 지출 기준)."""
    nq = qty + q
    return (cost * qty + spend) / nq if nq > 0 else 0.0


def _realized(q: float, px: float, fee: float, cost: float) -> float:
    """매도 실현손익 (수수료 차감)."""
    return q * px * (1 - fee) - q * cost


def build_indicators(prices: pd.DataFrame, tickers: list,
                     idx, s: dict) -> dict:
    """전략 관측용 지표 묶음. short 섹션 파라미터가 MACD/BB에 반영된다."""
    sh = s.get("short", {})
    return {
        "rsi": pd.DataFrame({t: rsi(prices[t], s["rsi_window"])
                             for t in tickers}, index=idx),
        "macd_hist": pd.DataFrame({t: macd_hist(
            prices[t], int(sh.get("macd_fast", 12)), int(sh.get("macd_slow", 26)),
            int(sh.get("macd_signal", 9))) for t in tickers}, index=idx),
        "pctb": pd.DataFrame({t: bollinger_pctb(
            prices[t], int(sh.get("bb_window", 20)),
            float(sh.get("bb_std", 2.0))) for t in tickers}, index=idx),
        "ma20": pd.DataFrame({t: ma(prices[t], 20) for t in tickers}, index=idx),
        "ma60": pd.DataFrame({t: ma(prices[t], 60) for t in tickers}, index=idx),
    }


def run(prices: pd.DataFrame, fund_units: pd.DataFrame, cfg: dict,
        strategy=None, start=None) -> dict:
    """strategy: 전략 플러그인 모듈(또는 이름). None이면 config의 module 사용.
    start 이전 행은 RSI 웜업용으로만 쓰고 매매하지 않는다 (설계 컷오프 준수)."""
    s = cfg["strategy"]
    if strategy is None:
        strategy = s.get("module", "example_value_rsi")
    if isinstance(strategy, str):
        strategy = load_strategy(strategy)
    tickers = list(prices.columns)
    idx = prices.index
    ind = build_indicators(prices, tickers, idx, s)

    def ctx_for(date):
        """전략에 넘기는 관측 컨텍스트 (당일까지 데이터만)."""
        return {"date": date, "prices": prices, "qty": dict(qty), "cash": cash,
                "total": total(prices.loc[date]), "ind": ind,
                "cost": dict(cost), "last_trade": dict(last_trade)}

    band = float(s.get("rebalance_band", 0.005))  # 리밸런싱 무거래 밴드

    start_ts = pd.Timestamp(start) if start else idx[0]
    trade_idx = idx[idx >= start_ts]
    if len(trade_idx) < 2:
        raise ValueError("백테스트 구간 데이터가 부족함(웜업 제외 후)")
    rebal_set = set(rebalance_dates(trade_idx, s["rebalance_freq"]))
    cap = float(cfg["initial_capital"])
    fee = float(cfg["costs"]["fee_rate"])

    cash = cap
    qty: dict[str, float] = {t: 0.0 for t in tickers}
    cost: dict[str, float] = {t: 0.0 for t in tickers}  # 평단 (수수료 포함)
    realized: dict[str, float] = {t: 0.0 for t in tickers}  # 누적 실현손익
    last_trade: dict[str, object] = {}  # 종목별 최근 거래일 (쿨다운용)
    trades: list[dict] = []
    snaps: list[dict] = []
    equity_curve: list[dict] = []
    daily_rows: list[dict] = []

    def total(px: pd.Series) -> float:
        return cash + sum(qty[t] * px[t] for t in tickers)

    def buy(t: str, amount: float, px: float, date, reason: str):
        nonlocal cash
        amount = min(amount, cash)
        if amount <= 0 or px <= 0:
            return
        q = amount / px
        spend = amount * (1 + fee)
        if spend > cash:
            q = cash / (px * (1 + fee))
            spend = cash
            amount = q * px
        if q <= 0:
            return
        cost[t] = _avg_cost(cost[t], qty[t], spend, q)
        qty[t] += q
        cash -= spend
        last_trade[t] = date
        trades.append({"date": date, "type": "BUY", "ticker": t, "qty": q,
                       "price": px, "amount": amount, "reason": reason,
                       "pnl": 0.0, "ret": 0.0})

    def sell(t: str, q: float, px: float, date, reason: str):
        nonlocal cash
        q = min(q, qty[t])
        if q <= 0 or px <= 0:
            return
        base = q * cost[t]
        pnl = _realized(q, px, fee, cost[t])
        realized[t] += pnl
        qty[t] -= q
        if qty[t] <= 1e-12:
            qty[t] = 0.0
            cost[t] = 0.0
        cash += q * px * (1 - fee)
        last_trade[t] = date
        trades.append({"date": date, "type": "SELL", "ticker": t, "qty": q,
                       "price": px, "amount": q * px, "reason": reason,
                       "pnl": pnl, "ret": pnl / base if base else 0.0})

    def snapshot(date, reason: str, dest=None):
        px = prices.loc[date]
        tot = total(px)
        row: dict = {"date": date, "reason": reason, "total": tot,
                     "cash": cash, "total_return": tot / cap - 1}
        for t in tickers:
            val = qty[t] * px[t]
            row[f"{t}_qty"] = qty[t]
            row[f"{t}_value"] = val
            row[f"{t}_w"] = val / tot if tot else 0.0
            row[f"{t}_cost"] = cost[t]
            row[f"{t}_ret"] = (px[t] / cost[t] - 1) if cost[t] > 0 else 0.0
        (dest if dest is not None else snaps).append(row)

    # 초기 매수: 백테스트 첫 영업일에 전략 목표비중 매수 (CASH 키 제외)
    first = trade_idx[0]
    tgt = strategy.targets(prices.loc[first], fund_units, cfg, ctx_for(first))
    px0 = prices.loc[first]
    for t, w in tgt.items():
        if t == "CASH" or t not in qty:
            continue
        buy(t, cap * w, px0[t], first, "INIT")
    snapshot(first, "INIT")
    snapshot(first, "DAILY", daily_rows)

    daily_y = float(cfg.get("cash_yield_annual", 0.0)) / 252
    for date in trade_idx[1:]:
        cash *= 1 + daily_y  # 현금(MMF) 일할 이자
        px = prices.loc[date]
        tot = total(px)
        # 1) 전술주문: 전략 플러그인이 반환한 주문 실행
        for o in strategy.tactical(date, px, ind["rsi"].loc[date], qty, cash, tot, cfg,
                                    ctx_for(date)) or []:
            t = o["ticker"]
            if t not in qty:
                continue
            if o["side"] == "BUY":
                buy(t, o.get("amount", 0.0), px[t], date, o.get("reason", "TACTICAL"))
            elif o["side"] == "SELL":
                q = o.get("qty", qty[t] * o.get("fraction", 1.0))
                sell(t, q, px[t], date, o.get("reason", "TACTICAL"))
        # 2) 정기 리밸런싱: 전략 목표비중으로 복원
        if date in rebal_set:
            tgt = strategy.targets(px, fund_units, cfg, ctx_for(date))
            tot = total(px)
            for t in tickers:  # 1패스: 매도 먼저 (현금 확보)
                want = tot * tgt.get(t, 0.0)
                have = qty[t] * px[t]
                if have - want > tot * band:
                    sell(t, (have - want) / px[t], px[t], date, "REBALANCE")
            for t in tickers:  # 2패스: 매수 (목표비중 복원 → 현금 10%)
                want = tot * tgt.get(t, 0.0)
                have = qty[t] * px[t]
                if want - have > tot * band:
                    buy(t, want - have, px[t], date, "REBALANCE")
            snapshot(date, "REBALANCE")
        elif trades and trades[-1]["date"] == date:
            snapshot(date, "TACTICAL")
        equity_curve.append({"date": date, "total": total(px), "cash": cash})
        snapshot(date, "DAILY", daily_rows)

    eq = pd.DataFrame(equity_curve).set_index("date")
    return {
        "trades": pd.DataFrame(trades),
        "snapshots": pd.DataFrame(snaps),
        "daily_holdings": pd.DataFrame(daily_rows),
        "equity": eq,
        "rsi": ind["rsi"],
    }

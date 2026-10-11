"""본인 전략 v2: 스윙 50% + 단기 40% + 현금 10% (2주 리밸런싱).

- 스윙: PER+PBR 상위 9개 각 10% + 현금 10% (상위 5개 코어 + 4개 단기풀).
- 단기 신호(signal 선택): rsi | macd | bb. 규칙·임계값은 config short 섹션.
- 헤드앤숄더 규칙: 편입외 보유종목이라도 상승추세 + 천장형 없음이면
  강제매도 면제(현 비중 유지).
"""
from __future__ import annotations

from ..factors import rank_at
from ..patterns import keep_winner

NAME = "my_strategy v2 (swing50+short40+cash10)"

N_TARGET = 9
W_EACH = 0.10
CASH_W = 0.10
MAX_STOCK_W = 0.90


def _short_cfg(cfg) -> dict:
    return cfg.get("strategy", {}).get("short", {})


def targets(price_row, fund_units, cfg, ctx=None) -> dict:
    ranked = list(rank_at(price_row, fund_units).index[:N_TARGET])
    picks = list(ranked)
    if ctx:
        # H&S 면제: 상승곡선 보유종목이 최하위 편입을 대체 (현금 10% 유지)
        prices, date = ctx["prices"], ctx["date"]
        keeps = [t for t, q in ctx["qty"].items()
                 if q > 0 and t not in picks and keep_winner(prices[t].loc[:date])]
        keeps = keeps[:N_TARGET]
        picks = keeps + [t for t in ranked if t not in keeps][:N_TARGET - len(keeps)]
    w = {t: W_EACH for t in picks}
    w["CASH"] = CASH_W
    return w


def _signal_buy(short: dict, t: str, ctx, date) -> bool:
    sig = short.get("signal", "rsi")
    ind = ctx["ind"]
    if sig == "macd":  # 히스토그램 양전환 매수
        h = ind["macd_hist"][t].loc[:date].tail(2)
        return len(h) == 2 and h.iloc[-2] <= 0 < h.iloc[-1]
    if sig == "bb":  # 하단 이탈 매수
        return bool(ind["pctb"][t].loc[date] < 0)
    return bool(ind["rsi"][t].loc[date] < short.get("rsi_buy", 25))


def _signal_sell(short: dict, t: str, ctx, date) -> bool:
    sig = short.get("signal", "rsi")
    ind = ctx["ind"]
    if sig == "macd":  # 히스토그램 음전환 청산
        h = ind["macd_hist"][t].loc[:date].tail(2)
        return len(h) == 2 and h.iloc[-2] >= 0 > h.iloc[-1]
    if sig == "bb":  # 상단 돌파 청산
        return bool(ind["pctb"][t].loc[date] > 1)
    return bool(ind["rsi"][t].loc[date] > short.get("rsi_sell", 65))


def tactical(date, px, rsi_row, qty, cash, total, cfg, ctx=None) -> list:
    short = _short_cfg(cfg)
    sig = short.get("signal", "rsi")
    cooldown = int(short.get("cooldown_days", 0))
    stop = float(short.get("stop_loss", 0.0) or 0.0)
    last = (ctx or {}).get("last_trade", {})
    acost = (ctx or {}).get("cost", {})
    orders = []
    stock_val = sum(qty.get(t, 0) * px[t] for t in px.index)
    for t in px.index:
        q = qty.get(t, 0)
        c = acost.get(t, 0.0) or 0.0
        if stop > 0 and q > 0 and c > 0 and px[t] <= c * (1 - stop):
            orders.append({"side": "SELL", "ticker": t, "fraction": 1.0,
                           "reason": "SHORT_STOP"})
            continue
        if q > 0 and _signal_sell(short, t, ctx, date):
            orders.append({"side": "SELL", "ticker": t, "fraction": 0.5,
                           "reason": f"SHORT_SELL({sig})"})
        elif q * px[t] < total * 0.01 and _signal_buy(short, t, ctx, date):
            if cooldown and t in last and (date - last[t]).days < cooldown:
                continue  # 최근 거래 종목 쿨다운 (회전율 억제)
            room = total * MAX_STOCK_W - stock_val
            if room > 0 and cash > 0:
                orders.append({"side": "BUY", "ticker": t,
                               "amount": min(cash * 0.5, room),
                               "reason": f"SHORT_BUY({sig})"})
    return orders

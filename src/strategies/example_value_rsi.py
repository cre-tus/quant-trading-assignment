"""테스트용 예시 전략 (과제 옵션1 데모). 제출용 전략이 아니다.

PER+PBR 합산랭크 상위 top_n + RSI 전술매매.
본인 전략은 my_strategy.py에 작성하고 config.yaml의 module만 교체한다.
"""
from __future__ import annotations

from ..factors import rank_at
from ..strategy import target_weights

NAME = "example_value_rsi (테스트용 예시)"


def targets(price_row, fund_units, cfg, ctx=None) -> dict:
    """종목→목표비중 dict (CASH 키 포함)."""
    s = cfg["strategy"]
    picks = list(rank_at(price_row, fund_units).index[: s["top_n"]])
    return target_weights(picks, s["weight_each"], s["cash_weight"])


def tactical(date, px, rsi_row, qty, cash, total, cfg, ctx=None) -> list:
    """일중 전술주문. BUY는 amount, SELL은 fraction/qty 중 하나."""
    s = cfg["strategy"]
    max_w = s["weight_each"] * (1 + s["band_expand"])
    orders = []
    for t in px.index:
        if qty.get(t, 0) > 0 and rsi_row[t] > s["rsi_sell"]:
            orders.append({"side": "SELL", "ticker": t, "fraction": 0.5,
                           "reason": f"RSI_SELL({rsi_row[t]:.1f})"})
    for t in px.index:
        if qty.get(t, 0) * px[t] < total * 0.01 and rsi_row[t] < s["rsi_buy"]:
            room = total * max_w - qty.get(t, 0) * px[t]
            orders.append({"side": "BUY", "ticker": t,
                           "amount": min(cash * 0.5, room),
                           "reason": f"RSI_BUY({rsi_row[t]:.1f})"})
    return orders

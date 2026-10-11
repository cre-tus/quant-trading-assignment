"""손절 규칙 테스트 (합성 컨텍스트, 외부 데이터 없음)."""
import unittest

import pandas as pd

from src.strategies.my_strategy import tactical


def _ctx(date, price, rsi_val=50.0, cost=100.0, qty=10.0):
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = pd.DataFrame({"A": [price] * len(idx)}, index=idx)
    ind = {"rsi": pd.DataFrame({"A": [rsi_val] * len(idx)}, index=idx)}
    return {"date": date, "prices": prices, "qty": {"A": qty}, "cash": 0.0,
            "total": qty * price, "ind": ind, "cost": {"A": cost},
            "last_trade": {}}


def _cfg(stop=None, sell=70):
    short = {"signal": "rsi", "rsi_buy": 20, "rsi_sell": sell,
             "cooldown_days": 0}
    if stop is not None:
        short["stop_loss"] = stop
    return {"strategy": {"short": short}}


class TestStopLoss(unittest.TestCase):
    def test_stop_fires_full_sell(self):
        date = pd.Timestamp("2024-03-01")
        ctx = _ctx(date, price=80.0)  # 평단 100 대비 -20%
        orders = tactical(date, pd.Series({"A": 80.0}), None,
                          {"A": 10.0}, 0.0, 800.0, _cfg(stop=0.15), ctx)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["reason"], "SHORT_STOP")
        self.assertEqual(orders[0]["fraction"], 1.0)

    def test_no_stop_above_line(self):
        date = pd.Timestamp("2024-03-01")
        ctx = _ctx(date, price=90.0)  # -10%, 손절선 위
        orders = tactical(date, pd.Series({"A": 90.0}), None,
                          {"A": 10.0}, 0.0, 900.0, _cfg(stop=0.15), ctx)
        self.assertEqual(orders, [])

    def test_no_stop_configured(self):
        date = pd.Timestamp("2024-03-01")
        ctx = _ctx(date, price=50.0)  # -50%라도 설정 없으면 발동 안 함
        orders = tactical(date, pd.Series({"A": 50.0}), None,
                          {"A": 10.0}, 0.0, 500.0, _cfg(stop=None), ctx)
        self.assertEqual(orders, [])

    def test_stop_priority_over_rsi_sell(self):
        date = pd.Timestamp("2024-03-01")
        ctx = _ctx(date, price=80.0, rsi_val=99.0)  # RSI 매도도 참
        orders = tactical(date, pd.Series({"A": 80.0}), None,
                          {"A": 10.0}, 0.0, 800.0, _cfg(stop=0.15), ctx)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["reason"], "SHORT_STOP")


if __name__ == "__main__":
    unittest.main()

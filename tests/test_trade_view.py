"""거래이력 뷰 테스트 (합성 미니 장부, 외부 데이터 없음)."""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.trade_view import build_trade_view, reason_kr


class TestTradeView(unittest.TestCase):
    def _mini(self, root: Path):
        pd.DataFrame([
            {"date": "2024-01-02", "type": "BUY", "ticker": "A", "qty": 10.0,
             "price": 100.0, "amount": 1000.0, "reason": "INIT",
             "pnl": 0.0, "ret": 0.0},
            {"date": "2024-01-10", "type": "SELL", "ticker": "A", "qty": 1000.0,
             "price": 120.0, "amount": 120000.0, "reason": "SHORT_SELL(rsi)",
             "pnl": 20000.0, "ret": 0.2},
        ]).to_csv(root / "trade_log.csv", index=False)
        pd.DataFrame({"total": [100000.0, 100200.0], "cash": [99000.0, 100200.0]},
                     index=pd.to_datetime(["2024-01-02", "2024-01-10"])
                     ).to_csv(root / "daily_equity.csv", index_label="date")

    def test_view_columns_and_math(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._mini(root)
            out = build_trade_view(root, fee_rate=0.001, names={"A": "에이"})
            v = pd.read_csv(out, encoding="utf-8-sig")
            self.assertEqual(len(v), 2)
            self.assertEqual(list(v.columns)[:5], ["순번", "날짜", "구분", "종목", "종목명"])
            self.assertEqual(v.loc[0, "구분"], "매수")
            self.assertEqual(v.loc[1, "종목명"], "에이")
            self.assertAlmostEqual(v.loc[1, "수수료"], 120.0)
            self.assertAlmostEqual(v.loc[1, "실현손익"], 20000.0)
            self.assertAlmostEqual(v.loc[1, "실현수익률%"], 20.0)
            self.assertAlmostEqual(v.loc[1, "종목누적실현손익"], 20000.0)
            self.assertEqual(v.loc[1, "보유일수"], 8)
            self.assertAlmostEqual(v.loc[1, "거래후총자산"], 100200.0)
            self.assertAlmostEqual(v.loc[1, "거래후누적수익률%"], 0.2)

    def test_reason_mapping_and_ticker_fallback(self):
        self.assertEqual(reason_kr("SHORT_SELL(rsi)"), "단기매도(RSI)")
        self.assertEqual(reason_kr("REBALANCE"), "리밸런싱")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._mini(root)
            v = pd.read_csv(build_trade_view(root, names={}), encoding="utf-8-sig")
            self.assertEqual(v.loc[0, "종목명"], "A")


if __name__ == "__main__":
    unittest.main()

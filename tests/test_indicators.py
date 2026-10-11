"""지표 파라미터 배선 테스트 (합성 시세, 외부 데이터 없음)."""
import unittest

import pandas as pd

from src.backtest import build_indicators
from src.indicators import bollinger_pctb, macd_hist, rsi


def _px() -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=120, freq="B")
    base = 100 + pd.Series(range(120)).apply(lambda i: (i % 10) - 4).cumsum().values
    return pd.DataFrame({"A": base}, index=idx)


class TestIndicatorParams(unittest.TestCase):
    def test_rsi_window_flows(self):
        px = _px()
        ind = build_indicators(px, ["A"], px.index, {"rsi_window": 7})
        pd.testing.assert_series_equal(
            ind["rsi"]["A"], rsi(px["A"], 7), check_names=False)

    def test_macd_params_flow_with_defaults(self):
        px = _px()
        dflt = build_indicators(px, ["A"], px.index, {"rsi_window": 14})
        pd.testing.assert_series_equal(
            dflt["macd_hist"]["A"], macd_hist(px["A"]), check_names=False)
        cust = build_indicators(px, ["A"], px.index,
                                {"rsi_window": 14,
                                 "short": {"macd_fast": 5, "macd_slow": 35,
                                           "macd_signal": 5}})
        pd.testing.assert_series_equal(
            cust["macd_hist"]["A"], macd_hist(px["A"], 5, 35, 5),
            check_names=False)
        self.assertFalse(cust["macd_hist"]["A"].equals(dflt["macd_hist"]["A"]))

    def test_bb_params_flow(self):
        px = _px()
        cust = build_indicators(px, ["A"], px.index,
                                {"rsi_window": 14,
                                 "short": {"bb_window": 10, "bb_std": 1.9}})
        pd.testing.assert_series_equal(
            cust["pctb"]["A"], bollinger_pctb(px["A"], 10, 1.9),
            check_names=False)


if __name__ == "__main__":
    unittest.main()

"""엔진 회귀테스트 (표준 unittest, 의존성 추가 없음)."""
import unittest
from pathlib import Path

import pandas as pd

from src.backtest import run
from src.data_loader import load_fundamentals, load_prices
from src.factors import rank_at, snapshot_units
from src.indicators import rsi
from src.metrics import buy_and_hold, strategy_metrics


def _demo_cfg():
    return {
        "initial_capital": 100000,
        "cash_yield_annual": 0.04,
        "strategy": {"top_n": 4, "weight_each": 0.20, "cash_weight": 0.20,
                     "band_expand": 0.20, "rebalance_freq": "4W",
                     "rsi_window": 14, "rsi_sell": 85, "rsi_buy": 20},
        "costs": {"fee_rate": 0.001},
    }


class TestEngine(unittest.TestCase):
    def test_rsi_bounds(self):
        px, _ = load_prices(["A", "B"], "2024-01-01", "2024-06-30", offline=True)
        for t in px.columns:
            v = rsi(px[t]).dropna()
            self.assertTrue(((v >= 0) & (v <= 100)).all())

    def test_rank_prefers_cheap(self):
        px, _ = load_prices(["A", "B"], "2024-01-01", "2024-02-29", offline=True)
        fund = pd.DataFrame({"trailingPE": [10.0, 40.0], "priceToBook": [1.0, 8.0]},
                            index=["A", "B"])
        units = snapshot_units(fund, px.iloc[0])
        self.assertEqual(rank_at(px.iloc[0], units).index[0], "A")

    def test_offline_backtest_produces_trades_and_metrics(self):
        tickers = ["A", "B", "C", "D", "E"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-12-31", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20, 30, 40],
                             "priceToBook": [1, 2, 3, 5, 9]}, index=tickers)
        out = run(px, snapshot_units(fund, px.iloc[0]), _demo_cfg())
        self.assertGreater(len(out["trades"]), 0)
        self.assertGreater(len(out["equity"]), 0)
        m = strategy_metrics(out["equity"]["total"])
        for k in ("CAGR", "MDD", "total_return", "sharpe"):
            self.assertIn(k, m)
        self.assertLessEqual(m["MDD"], 0.0)

    def test_empty_equity_raises_clear_error(self):
        with self.assertRaises(ValueError):
            strategy_metrics(pd.Series(dtype=float))

    def test_warmup_rows_not_traded(self):
        px, _ = load_prices(["A", "B", "C"], "2023-10-01", "2024-03-31", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=["A", "B", "C"])
        cfg = _demo_cfg()
        out = run(px, snapshot_units(fund, px.iloc[0]), cfg, start="2024-01-01")
        self.assertTrue((out["equity"].index >= "2024-01-01").all())
        self.assertTrue((out["trades"]["date"] >= "2024-01-01").all())

    def test_manual_fy2023_fundamentals_preferred(self):
        import os
        import tempfile
        tickers = ["A", "B"]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "fy2023.csv")
            pd.DataFrame({"trailingPE": [11.0, 22.0], "priceToBook": [1.5, 2.5]},
                         index=pd.Index(tickers, name="ticker")).to_csv(p)
            before = Path("data/fundamentals_snapshot.csv").read_bytes()
            df, src = load_fundamentals(tickers, offline=False, manual_path=p,
                                        write_cache=False)
            # 테스트가 실 캐시를 덮어쓰면 안 됨
            self.assertEqual(Path("data/fundamentals_snapshot.csv").read_bytes(),
                             before)
        self.assertEqual(df.loc["A", "trailingPE"], 11.0)
        self.assertIn("manual", src)

    def test_analysis_runs_on_any_plugin_result(self):
        from src.analysis import analyze
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-06-30", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        cfg = _demo_cfg()
        out = run(px, snapshot_units(fund, px.iloc[0]), cfg)
        m = strategy_metrics(out["equity"]["total"])
        bh = buy_and_hold(px, 100000)
        a = analyze(out["equity"]["total"], bh, out["trades"],
                    out["snapshots"], px, cfg, m, 0.05)
        self.assertTrue(a["lines"])
        self.assertGreaterEqual(a["facts"]["turnover"], 0.0)
        # 빈 거래(현금 기준선)에서도 동작해야 함
        cfg["strategy"]["module"] = "my_strategy"
        out2 = run(px, snapshot_units(fund, px.iloc[0]), cfg)
        m2 = strategy_metrics(out2["equity"]["total"])
        a2 = analyze(out2["equity"]["total"], bh, out2["trades"],
                     out2["snapshots"], px, cfg, m2, 0.05)
        self.assertTrue(a2["lines"])

    def test_load_universe_skips_comments_and_dupes(self):
        import os
        import tempfile
        from src.data_loader import load_universe
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "uni.txt")
            Path(p).write_text("# 주석\naapl\nMSFT\naapl\n\n", encoding="utf-8")
            self.assertEqual(load_universe(p), ["AAPL", "MSFT"])

    def test_head_and_shoulders_top_vs_uptrend(self):
        import numpy as np
        from src.patterns import head_and_shoulders_top, keep_winner, uptrend_intact
        hs = np.concatenate([np.linspace(90, 100, 15), np.linspace(100, 95, 8),
                             np.linspace(95, 110, 12), np.linspace(110, 96, 8),
                             np.linspace(96, 101, 10), np.linspace(101, 96, 8),
                             np.linspace(96, 88, 18)])
        s_hs = pd.Series(hs)
        self.assertTrue(head_and_shoulders_top(s_hs, lookback=len(s_hs)))
        s_up = pd.Series(np.linspace(100, 150, 70))
        self.assertFalse(head_and_shoulders_top(s_up))
        self.assertTrue(uptrend_intact(s_up))
        self.assertTrue(keep_winner(s_up))
        self.assertFalse(keep_winner(s_hs))

    def test_signal_switch_reflected_in_reasons(self):
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-06-30", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        cfg = _demo_cfg()
        cfg["strategy"]["module"] = "my_strategy"
        cfg["strategy"]["short"] = {"signal": "bb"}
        out = run(px, snapshot_units(fund, px.iloc[0]), cfg)
        shorts = out["trades"][out["trades"]["reason"].str.startswith("SHORT_")]
        self.assertTrue(all(r.endswith("(bb)") for r in shorts["reason"]))

    def test_rebalance_exempts_winner_only_when_intact(self):
        from src.factors import rank_at
        from src.patterns import keep_winner
        from src.strategies import my_strategy
        tickers = [chr(ord("A") + i) for i in range(10)]
        px, _ = load_prices(tickers, "2024-01-01", "2024-12-31", offline=True)
        fund = pd.DataFrame({"trailingPE": list(range(10, 110, 10)),
                             "priceToBook": list(range(1, 11))}, index=tickers)
        units = snapshot_units(fund, px.iloc[0])
        cfg = _demo_cfg()
        out_ticker = list(rank_at(px.iloc[-1], units).index)[9]  # 동적 랭킹 10위
        plain = my_strategy.targets(px.iloc[-1], units, cfg, None)
        self.assertNotIn(out_ticker, plain)  # 편입외 확인
        qty = {t: 0.0 for t in tickers}
        qty[out_ticker] = 5.0
        ctx = {"prices": px, "date": px.index[-1], "qty": qty,
               "cash": 1000.0, "total": 100000.0}
        with_ctx = my_strategy.targets(px.iloc[-1], units, cfg, ctx)
        self.assertEqual(out_ticker in with_ctx, keep_winner(px[out_ticker]))
        # 면제 여부와 무관하게 편입 9개 + 현금 10% 고정
        self.assertEqual(len([k for k in with_ctx if k != "CASH"]), 9)
        self.assertEqual(with_ctx["CASH"], 0.1)

    def test_cost_helpers_exact(self):
        from src.backtest import _avg_cost, _realized
        self.assertAlmostEqual(_avg_cost(0.0, 0.0, 1010.0, 10.0), 101.0)
        self.assertAlmostEqual(_avg_cost(101.0, 10.0, 2020.0, 20.0),
                               (1010.0 + 2020.0) / 30)
        self.assertAlmostEqual(_realized(10.0, 120.0, 0.001, 101.0),
                               10 * 120 * 0.999 - 1010.0)

    def test_daily_holdings_cover_every_day(self):
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-06-30", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        out = run(px, snapshot_units(fund, px.iloc[0]), _demo_cfg())
        self.assertIn("pnl", out["trades"].columns)
        self.assertTrue(pd.to_numeric(out["trades"]["pnl"],
                                      errors="coerce").notna().all())
        self.assertTrue(set(out["equity"].index)
                        <= set(out["daily_holdings"]["date"]))
        self.assertEqual(len(out["daily_holdings"]), len(out["equity"]) + 1)
        self.assertIn("A_cost", out["daily_holdings"].columns)
        self.assertIn("A_ret", out["daily_holdings"].columns)

    def test_excel_workbook_has_formatted_sheets(self):
        import os
        import tempfile
        from src.excel_report import build_workbook
        with tempfile.TemporaryDirectory() as d:
            pd.DataFrame({"date": ["2023-01-03", "2023-01-04"],
                          "total": [1.0, 2.0]}).to_csv(
                              os.path.join(d, "daily_holdings.csv"), index=False)
            pd.DataFrame({"ticker": ["A"],
                          "total_pnl": [1.0]}).to_csv(
                              os.path.join(d, "discovery.csv"), index=False)
            pd.DataFrame({"date": ["2023-01-03"], "type": ["BUY"]}).to_csv(
                os.path.join(d, "trade_log.csv"), index=False)
            out = build_workbook(d)
            self.assertTrue(os.path.exists(out))
            from openpyxl import load_workbook
            wb = load_workbook(out)
            self.assertEqual(set(wb.sheetnames),
                             {"일별보유", "종목손익", "거래기록"})
            ws = wb["일별보유"]
            self.assertEqual(ws.column_dimensions["A"].width, 13)
            self.assertEqual(ws["A2"].number_format, "yyyy-mm-dd")

    def test_buy_cooldown_skips_recent_ticker(self):
        import numpy as np
        from src.indicators import rsi as rsi_fn
        from src.strategies import my_strategy
        dates = pd.bdate_range("2024-01-01", periods=40)
        px = pd.DataFrame({"A": np.linspace(100, 60, 40)}, index=dates)
        rsi_df = pd.DataFrame({"A": rsi_fn(px["A"])}, index=dates)
        date = dates[-1]
        self.assertLess(rsi_df.loc[date, "A"], 25)
        qty = {"A": 0.0}
        cfg = _demo_cfg()
        cfg["strategy"]["module"] = "my_strategy"
        cfg["strategy"]["short"] = {"signal": "rsi", "rsi_buy": 25,
                                    "cooldown_days": 5}
        free = my_strategy.tactical(date, px.loc[date], rsi_df.loc[date], qty,
                                    100000.0, 100000.0, cfg,
                                    {"ind": {"rsi": rsi_df}, "last_trade": {}})
        self.assertEqual(len(free), 1)
        cool = my_strategy.tactical(date, px.loc[date], rsi_df.loc[date], qty,
                                    100000.0, 100000.0, cfg,
                                    {"ind": {"rsi": rsi_df},
                                     "last_trade": {"A": date - pd.Timedelta(days=2)}})
        self.assertEqual(len(cool), 0)

    def test_rebalance_band_suppresses_rebalance_trades(self):
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-06-30", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        cfg = _demo_cfg()
        cfg["strategy"]["rebalance_band"] = 1.0
        out = run(px, snapshot_units(fund, px.iloc[0]), cfg)
        self.assertNotIn("REBALANCE", set(out["trades"]["reason"]))

    def test_merge_frames_prefers_existing(self):
        from src.data_loader import merge_frames
        idx = pd.bdate_range("2024-01-01", periods=5)
        old = pd.DataFrame({"A": [1.0] * 5}, index=idx)
        new = pd.DataFrame({"A": [9.0] * 5, "B": [2.0] * 5}, index=idx)
        merged = merge_frames(old, new)
        self.assertEqual(merged["A"].tolist(), [1.0] * 5)
        self.assertIn("B", merged.columns)
        self.assertTrue(merge_frames(None, new).equals(new.sort_index()))

    def test_parse_nasdaq_drops_test_and_etf(self):
        from src.universe import _parse_nasdaq
        lines = ["Symbol|Name|Cat|Test|Fin|Lot|ETF|Next",
                 "AAPL|Apple Inc.|Q|N|N|100|N|N",
                 "TST|A Test Issue|Q|Y|N|100|N|N",
                 "SPY|SPDR ETF|Q|N|N|100|Y|N"]
        rows = _parse_nasdaq(lines, "NASDAQ")
        self.assertEqual([r["ticker"] for r in rows], ["AAPL"])
        olines = ["ACT|Name|Ex|CQS|ETF|Lot|Test|NSDQ",
                  "BRK/B|Berkshire|N|BRK.B|N|100|N|BRK.B",
                  "QQQ|Nasdaq ETF|Q|QQQ|Y|100|N|QQQ"]
        orows = _parse_nasdaq(olines, "OTHER")
        self.assertEqual([r["ticker"] for r in orows], ["BRK.B"])

    def test_korean_names_with_ticker_fallback(self):
        from src.names import load_names, name_of
        names = load_names("data/stock_names_kr.csv")
        self.assertEqual(name_of("aapl", names), "애플")
        self.assertEqual(name_of("ZZZ", names), "ZZZ")
        self.assertEqual(len(names), 60)

    def test_discovery_includes_exited_ticker_and_slim(self):
        from src.discovery import discovery_report, slim_daily
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-06-30", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        out = run(px, snapshot_units(fund, px.iloc[0]), _demo_cfg())
        # 전량 청산된 종목도 거래 기록 기준 포함
        daily = out["daily_holdings"].copy()
        for c in list(daily.columns):
            if c.rsplit("_", 1)[0] == "C":
                daily[c] = 0.0  # C 미보유 가정
        slim = slim_daily(daily, max_cols=10)
        self.assertNotIn("C_qty", slim.columns)
        self.assertIn("A_qty", slim.columns)
        disc = discovery_report(out["trades"], slim)
        traded = set(out["trades"]["ticker"].unique()) if len(out["trades"]) else set()
        self.assertTrue(traded <= set(disc["ticker"]))
        self.assertEqual(list(disc.columns)[:2], ["ticker", "name_kr"])

    def test_discovery_sorted_by_pnl(self):
        from src.discovery import discovery_report
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-06-30", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        out = run(px, snapshot_units(fund, px.iloc[0]), _demo_cfg())
        disc = discovery_report(out["trades"], out["daily_holdings"])
        self.assertEqual(set(disc["ticker"]), set(tickers))
        vals = disc["total_pnl"].tolist()
        self.assertEqual(vals, sorted(vals, reverse=True))

    def test_resolve_period_separates_experiment_and_final(self):
        from src.strategy import resolve_period
        cfg = {"start": "2024-01-01", "end": "2025-12-31",
               "warmup_start": "2023-10-01", "design_cutoff": "2023-12-31",
               "outputs": {"dir": "outputs"}}
        exp = resolve_period(cfg, "experiment")
        self.assertEqual((exp["cutoff"], exp["start"], exp["end"]),
                         ("2022-12-31", "2023-01-01", "2023-12-31"))
        self.assertEqual(exp["outdir"], "outputs_exp")
        fin = resolve_period(cfg, "final")
        self.assertEqual((fin["cutoff"], fin["start"], fin["end"]),
                         ("2023-12-31", "2024-01-01", "2025-12-31"))
        self.assertEqual(fin["outdir"], "outputs")

    def test_filter_common_drops_non_stock(self):
        from src.universe import filter_common
        df = pd.DataFrame({
            "ticker": ["AAPL", "ABCW", "BRK.B", "SPY", "XYZ-U"],
            "title": ["Apple Inc.", "Abc Warrant", "Berkshire Hathaway",
                      "SPDR S&P 500 ETF Trust", "Xyz Unit"],
            "cik_str": [1, 2, 3, 4, 5]})
        self.assertEqual(filter_common(df)["ticker"].tolist(), ["AAPL"])

    def test_edgar_picks_latest_filed_before_cutoff(self):
        from src.edgar import _fy_value
        facts = {"facts": {"us-gaap": {"EarningsPerShareDiluted": {"units": {
            "USD/shares": [
                {"fy": 2023, "fp": "FY", "form": "10-K",
                 "filed": "2024-02-01", "val": 5.0},
                {"fy": 2022, "fp": "FY", "form": "10-K",
                 "filed": "2023-02-01", "val": 4.0},
                {"fy": 2023, "fp": "Q4", "form": "10-Q",
                 "filed": "2023-10-01", "val": 9.9},
            ]}}}}}
        # 2024 공시·10-Q 제외 → 컷오프 이전 최신 10-K인 FY2022 값
        self.assertEqual(_fy_value(facts, ["EarningsPerShareDiluted"],
                                  "2023-12-31"), 4.0)

    def test_filter_liquid_uses_pre_cutoff_only(self):
        from src.data_loader import filter_liquid
        dates = pd.bdate_range("2023-10-01", "2024-01-31")
        close = pd.DataFrame({"BIG": 100.0, "SMALL": 1.0}, index=dates)
        vol = pd.DataFrame({"BIG": 1_000_000.0, "SMALL": 100.0}, index=dates)
        kept, stats = filter_liquid(close, vol, "2023-12-31",
                                    min_dollar_vol=1_000_000, lookback=60)
        self.assertEqual(kept, ["BIG"])
        self.assertEqual(stats["universe"], 2)

    def test_cross_check_agrees_with_ours(self):
        from src.metrics import cross_check
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-12-31", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        out = run(px, snapshot_units(fund, px.iloc[0]), _demo_cfg())
        m = strategy_metrics(out["equity"]["total"])
        cc = cross_check(out["equity"]["total"])
        self.assertTrue(cc.get("available"), cc.get("reason"))
        self.assertAlmostEqual(m["CAGR"], cc["values"]["annual_return"], delta=0.02)
        self.assertAlmostEqual(m["MDD"], cc["values"]["max_drawdown"], delta=0.005)
        self.assertAlmostEqual(m["sharpe"], cc["values"]["sharpe_ratio"], delta=0.05)

    def test_my_strategy_v1_builds_swing_positions(self):
        tickers = ["A", "B", "C"]
        px, _ = load_prices(tickers, "2024-01-01", "2024-03-31", offline=True)
        fund = pd.DataFrame({"trailingPE": [10, 15, 20],
                             "priceToBook": [1, 2, 3]}, index=tickers)
        cfg = _demo_cfg()
        cfg["strategy"]["module"] = "my_strategy"
        out = run(px, snapshot_units(fund, px.iloc[0]), cfg)
        self.assertGreater(len(out["equity"]), 0)
        # v1은 스윙 매수하므로 INIT 거래가 생긴다 (현금 기준선 아님)
        inits = out["trades"][out["trades"]["reason"] == "INIT"]
        self.assertGreater(len(inits), 0)
        self.assertLessEqual(len(inits), 3)
        # 단기 명칭으로 개명: SCALP 사유는 남아 있지 않아야 함
        self.assertFalse(any(str(r).startswith("SCALP")
                             for r in out["trades"]["reason"]))


if __name__ == "__main__":
    unittest.main()

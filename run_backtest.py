"""엔트리포인트: 설정 로드 → 데이터 → 백테스트 → 지표 → 차트/PPT 저장.

사용법(프로젝트 루트, .venv 활성화 후):
  python run_backtest.py                 # 온라인(yfinance) 시도
  python run_backtest.py --offline       # 합성 데모데이터로 실행(검증용)
  python run_backtest.py --freq 2W       # 리밸런싱 주기 오버라이드
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import pandas as pd
import yaml

from src.analysis import analyze
from src.backtest import run
from src.data_loader import load_fundamentals, load_prices, load_universe
from src.discovery import discovery_report
from src.strategy import resolve_period
from src.factors import snapshot_units
from src.metrics import buy_and_hold, cross_check, strategy_metrics
from src.report import build_pptx, equity_chart


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--freq", default=None, help="1W|2W|4W|M|Q")
    ap.add_argument("--universe", default=None, help="edgar|pool|file|config")
    ap.add_argument("--max-tickers", type=int, default=None,
                    help="유동성 상위 N개만(연기·테스트용)")
    ap.add_argument("--mode", default=None, help="experiment|final")
    ap.add_argument("--outdir", default=None, help="산출물 폴더 오버라이드")
    ap.add_argument("--signal", default=None, help="rsi|macd|bb (단기 신호 교체)")
    ap.add_argument("--set", action="append", default=[],
                    help="config 덮어쓰기 (예: strategy.short.rsi_buy=20)")
    ap.add_argument("--workers", type=int, default=8, help="시세 수집 스레드 수")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.freq or args.signal or args.set:
        cfg = copy.deepcopy(cfg)
        if args.freq:
            cfg["strategy"]["rebalance_freq"] = args.freq
        if args.signal:
            cfg["strategy"].setdefault("short", {})["signal"] = args.signal
        for ov in args.set:
            key, _, val = ov.partition("=")
            try:
                val_parsed = yaml.safe_load(val)
            except Exception:
                val_parsed = val
            node = cfg
            *path, last = key.split(".")
            for p in path:
                node = node.setdefault(p, {})
            node[last] = val_parsed

    mode = args.mode or cfg.get("mode", "experiment")
    P = resolve_period(cfg, mode)
    cutoff, warmup = P["cutoff"], P["warmup"]
    usrc = args.universe or cfg.get("universe_source", "file")
    cik_of: dict = {}
    if args.offline:
        upath = Path("data/universe_us.txt")
        universe = load_universe(str(upath)) if upath.exists() else list(cfg["universe"])
        list_src = "file(demo)"
    elif usrc == "pool":
        universe = [ln.strip().upper() for ln in
                    Path("data/pool_tickers.txt").read_text(encoding="utf-8").splitlines()
                    if ln.strip()]
        list_src = "pool"
        try:
            cik_of = {k: int(v) for k, v in
                      json.loads(Path("data/pool_cik.json").read_text(encoding="utf-8")).items()}
        except Exception:
            cik_of = {}
    elif usrc == "edgar":
        from src.universe import fetch_all_listings, filter_common
        df_list, list_src = fetch_all_listings(offline=False)
        df_list = filter_common(df_list)
        universe = df_list["ticker"].tolist()
        cik_of = dict(zip(df_list["ticker"], df_list["cik_str"]))
    elif usrc == "file":
        universe = load_universe(cfg["universe_file"])
        list_src = "file"
    else:
        universe = list(cfg["universe"])
        list_src = "config"
    print(f"[universe] {len(universe)}종목 ({list_src})")

    from src.data_loader import filter_liquid, load_market_data
    if args.offline:
        prices, vol, price_src = load_market_data(universe, warmup, P["end"],
                                                 offline=True)
    elif usrc == "pool" and Path("data/prices_full.csv").exists():
        prices = pd.read_csv("data/prices_full.csv", index_col=0, parse_dates=True)
        prices = prices.loc[warmup:P["end"]]
        vpath = Path("data/volumes_full.csv")
        vol = pd.read_csv(vpath, index_col=0,
                          parse_dates=True).reindex(prices.index) if vpath.exists() else None
        prices = prices[[c for c in universe if c in prices.columns]]
        prices = prices.ffill()  # delist tail NaN -> last-price flatline (leading NaN kept, no lookahead)
        price_src = "disk cache (pool)"
    else:
        prices, vol, price_src = load_market_data(universe, warmup, P["end"],
                                                 workers=args.workers)
        Path("data").mkdir(parents=True, exist_ok=True)
        prices.to_csv("data/prices.csv")
    kept, liq = filter_liquid(prices, vol, cutoff,
                              cfg.get("min_dollar_vol", 1_000_000))
    if args.max_tickers and vol is not None and len(kept) > args.max_tickers:
        win = vol.loc[vol.index <= pd.Timestamp(cutoff)].tail(60)
        dvol = (prices.reindex(win.index)[kept] * win[kept]).mean()
        kept = dvol.sort_values(ascending=False).head(args.max_tickers).index.tolist()
    print(f"[liquid] {liq['universe']} → {len(kept)}종목 "
          f"(컷오프 이전 60일 일대금 ≥ {cfg.get('min_dollar_vol', 1_000_000):,})")
    prices = prices[kept]

    fund_mode = cfg.get("fund_mode", "snapshot")
    if args.offline:
        fund, fund_src = load_fundamentals(kept, offline=True)
        ref_price = prices.loc[prices.index >= pd.Timestamp(P["start"])].iloc[0]
    elif fund_mode == "edgar" and cik_of:
        from src.edgar import fy_snapshot
        px_cut = prices.loc[prices.index <= pd.Timestamp(cutoff)]
        if len(px_cut) == 0:
            raise ValueError("컷오프 이전 시세 없음 — warmup 기간 확인")
        px0 = px_cut.iloc[-1]
        fund = fy_snapshot(kept, cik_of, px0, cutoff)
        mp = Path("data/fundamentals_fy2023.csv")  # 수동 확정치가 있으면 우선
        n_man = 0
        if mp.exists():
            try:
                man = pd.read_csv(mp, index_col=0, comment="#")
                man = man.apply(pd.to_numeric, errors="coerce").dropna()
                fund.update(man)
                n_man = len(set(man.index) & set(kept))
            except Exception as e:
                print(f"[data] 수동 병합 실패({e})")
        fund.to_csv("data/fundamentals_snapshot.csv")
        n_ed = int(fund["trailingPE"].notna().sum())
        fund_src = (f"edgar FY(filed<={cutoff}) + manual({n_man}) - "
                    f"{n_ed}/{len(kept)}종목 확보, 결측 최하위")
        ref_price = px0
    else:
        if fund_mode == "edgar":
            print("[fund] CIK 매핑 없음 → snapshot 모드로 폴백")
        fund, fund_src = load_fundamentals(kept, offline=False)
        ref_price = prices.loc[prices.index >= pd.Timestamp(P["start"])].iloc[0]
    # 백테스트 구간만 분리: warmup 구간은 RSI 시동용, 매매·지표에서 제외
    px = prices.loc[prices.index >= pd.Timestamp(P["start"])]
    units = snapshot_units(fund, ref_price)

    strat_name = cfg["strategy"].get("module", "example_value_rsi")
    out = run(prices, units, cfg, strat_name, start=P["start"])
    m = strategy_metrics(out["equity"]["total"])
    bh = buy_and_hold(px, float(cfg["initial_capital"]))
    bh_ret = float(bh.iloc[-1] / bh.iloc[0] - 1)

    odir = Path(args.outdir or P["outdir"])
    odir.mkdir(parents=True, exist_ok=True)
    out["trades"].to_csv(odir / "trade_log.csv", index=False)
    out["snapshots"].to_csv(odir / "holdings_snapshots.csv", index=False)
    from src.discovery import slim_daily
    out["daily_holdings"] = slim_daily(out["daily_holdings"])
    out["daily_holdings"].to_csv(odir / "daily_holdings.csv", index=False)
    from src.names import load_names
    disc = discovery_report(out["trades"], out["daily_holdings"], load_names())
    disc.to_csv(odir / "discovery.csv", index=False)
    out["equity"].to_csv(odir / "daily_equity.csv")
    cc = cross_check(out["equity"]["total"])
    (odir / "metrics.json").write_text(
        json.dumps({"strategy": m, "strategy_module": strat_name,
                    "buy_and_hold_return": bh_ret,
                    "design_cutoff": cutoff, "test_start": P["start"],
                    "mode": mode,
                    "price_source": price_src, "fund_source": fund_src,
                    "n_trades": len(out["trades"]), "cross_check": cc,
                    "universe": {"source": list_src, "listed": len(universe),
                                 "liquid": len(kept)}},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    analysis = analyze(out["equity"]["total"], bh, out["trades"],
                       out["snapshots"], px, cfg, m, bh_ret)
    (odir / "analysis.json").write_text(
        json.dumps(analysis["facts"], ensure_ascii=False, indent=2), encoding="utf-8")
    (odir / "analysis.md").write_text(
        f"# 결과 분석·평가 (자동 생성, 전략: {strat_name})\n\n"
        + "\n".join(f"- {l}" if l.startswith("[") else l for l in analysis["lines"])
        + "\n", encoding="utf-8")

    chart = str(odir / "equity_curve.png")
    equity_chart(out["equity"]["total"], bh, chart)
    build_pptx(cfg, m, bh_ret, fund, fund_src, price_src, len(out["trades"]),
               chart, str(odir / "report.pptx"), analysis["lines"],
               universe_info=f"{list_src} {len(universe)}→유동성 {len(kept)}",
               outdir=odir.name, strat_name=strat_name)
    try:
        from src.excel_report import build_workbook
        print(f"  엑셀 → {build_workbook(odir)}")
    except Exception as e:
        print(f"  [엑셀] 생략: {e}")
    try:
        from src.trade_view import build_trade_view
        print(f"  거래이력뷰 → {build_trade_view(odir, float(cfg['costs']['fee_rate']))}")
    except Exception as e:
        print(f"  [거래이력뷰] 생략: {e}")

    f = analysis["facts"]
    print(f"[mode={mode}] 설계 ≤ {cutoff}, 백테스트 {P['start']}~{P['end']} "
          f"(warmup {warmup}~)")
    print(f"[done] strategy={strat_name} price={price_src} fund={fund_src} "
          f"trades={len(out['trades'])}")
    print(f"  CAGR={m['CAGR']:.2%}  B&H={bh_ret:.2%}  MDD={m['MDD']:.2%}  "
          f"Sharpe={m['sharpe']:.2f}")
    if cc.get("available"):
        v = cc["values"]
        print(f"  [교차] ann_ret={v['annual_return']:.2%} mdd={v['max_drawdown']:.2%} "
              f"sharpe={v['sharpe_ratio']:.2f} sortino={v['sortino_ratio']:.2f} "
              f"calmar={v['calmar_ratio']:.2f}")
    else:
        print(f"  [교차] 불가: {cc.get('reason')}")
    print(f"  회전율={f['turnover']}배 수수료추정={f['fee_est']:,.0f} "
          f"전고회복={f['recovery_days']}일 초과수익={f['excess_vs_bh']:.1%}")
    if len(disc):
        top = disc.head(3)[["ticker", "total_pnl"]].values.tolist()
        bot = disc.tail(3)[["ticker", "total_pnl"]].values.tolist()
        print(f"  종목손익 top3: {top} / bottom3: {bot}")
    print(f"  outputs → {odir.resolve()}")


if __name__ == "__main__":
    main()

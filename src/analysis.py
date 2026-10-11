"""결과 분석·평가 자동화 (과제 제출 4번: 좋은 점/나쁜 점 + 원인 분석).

백테스트 산출물(지표·거래·스냅샷·가격)만으로 평가 리포트를 만든다.
전략 로직을 건드리지 않으므로 어떤 플러그인 결과에도 그대로 적용된다.
"""
from __future__ import annotations

import pandas as pd


SELL_PREFIXES = ("RSI_SELL", "SHORT_SELL")
BUY_PREFIXES = ("RSI_BUY", "SHORT_BUY")


def _fwd_mean(prices: pd.DataFrame, trades: pd.DataFrame, prefixes: tuple,
              days: int = 20):
    """전술 매매 후 20영업일 수익률 평균 (사후 평가용 — 전략 판단에 쓰지 않음)."""
    if not len(trades):
        return None
    vals = []
    for _, r in trades[trades["reason"].str.startswith(prefixes)].iterrows():
        try:
            fut = prices.index[prices.index > pd.Timestamp(r["date"])][:days]
            if len(fut) < days:
                continue
            base = prices.loc[pd.Timestamp(r["date"]), r["ticker"]]
            vals.append(float(prices.loc[fut[-1], r["ticker"]] / base - 1))
        except (KeyError, TypeError):
            continue
    return (sum(vals) / len(vals)) if vals else None


def analyze(equity: pd.Series, bh: pd.Series, trades: pd.DataFrame,
            snapshots: pd.DataFrame, prices: pd.DataFrame,
            cfg: dict, m: dict, bh_ret: float) -> dict:
    """facts(수치 dict) + lines(PPT·md용 불릿) 반환."""
    eq = equity.dropna()
    cap = float(cfg["initial_capital"])
    fee_rate = float(cfg["costs"]["fee_rate"])
    traded = float(trades["amount"].sum()) if len(trades) else 0.0
    fee_est = traded * fee_rate
    turnover = traded / eq.mean() if len(eq) and eq.mean() else 0.0
    reasons = trades["reason"].value_counts().to_dict() if len(trades) else {}
    n_sell = int(trades["reason"].str.startswith(SELL_PREFIXES).sum()) if len(trades) else 0
    n_buy = int(trades["reason"].str.startswith(BUY_PREFIXES).sum()) if len(trades) else 0
    fwd_sell = _fwd_mean(prices, trades, SELL_PREFIXES)
    fwd_buy = _fwd_mean(prices, trades, BUY_PREFIXES)

    buys = trades[trades["type"] == "BUY"] if len(trades) else trades
    top_picks = buys["ticker"].value_counts().head(4).to_dict() if len(buys) else {}
    wcols = [c for c in snapshots.columns if c.endswith("_w")] if len(snapshots) else []
    avg_w = snapshots[wcols].mean().sort_values(ascending=False).head(3).to_dict() \
        if wcols else {}

    mo = eq.resample("ME").last().pct_change().dropna()
    best = (str(mo.idxmax().date()), float(mo.max())) if len(mo) else (None, None)
    worst = (str(mo.idxmin().date()), float(mo.min())) if len(mo) else (None, None)
    neg_m = int((mo < 0).sum())

    rec_days = None
    if m.get("MDD_peak") and m.get("MDD_trough"):
        peak = eq.loc[:m["MDD_peak"]].max()
        after = eq.loc[m["MDD_trough"]:]
        hit = after[after >= peak]
        if len(hit):
            rec_days = (hit.index[0] - pd.Timestamp(m["MDD_trough"])).days

    fee_free = (eq.iloc[-1] + fee_est) / eq.iloc[0] - 1 if len(eq) else 0.0
    excess = float(m["total_return"] - bh_ret)
    bh_each = (prices.iloc[-1] / prices.iloc[0] - 1).sort_values(ascending=False)
    top_bh = (str(bh_each.index[0]), float(bh_each.iloc[0])) if len(bh_each) else (None, None)

    facts = {
        "turnover": round(float(turnover), 3),
        "fee_est": round(float(fee_est), 2),
        "fee_pct_of_cap": round(float(fee_est / cap), 4),
        "trades_by_reason": {str(k): int(v) for k, v in reasons.items()},
        "rsi_sells": n_sell, "rsi_buys": n_buy,
        "rsi_sell_fwd20_mean": None if fwd_sell is None else round(fwd_sell, 4),
        "rsi_buy_fwd20_mean": None if fwd_buy is None else round(fwd_buy, 4),
        "top_picks": {str(k): int(v) for k, v in top_picks.items()},
        "avg_weights_top3": {str(k).removesuffix("_w"): round(float(v), 3)
                             for k, v in avg_w.items()},
        "best_month": {"date": best[0], "ret": best[1]},
        "worst_month": {"date": worst[0], "ret": worst[1]},
        "neg_months": neg_m, "total_months": len(mo),
        "recovery_days": rec_days,
        "fee_free_total_return": round(float(fee_free), 4),
        "excess_vs_bh": round(float(excess), 4),
        "top_bh_ticker": {"ticker": top_bh[0], "ret": top_bh[1]},
    }

    good, bad = [], []
    (good if m["CAGR"] > 0 else bad).append(f"CAGR {m['CAGR']:.1%}")
    (good if excess > 0 else bad).append(
        f"B&H 대비 초과수익 {excess:+.1%} (B&H {bh_ret:.1%})")
    (good if m["MDD"] > -0.15 else bad).append(f"MDD {m['MDD']:.1%}")
    (good if m["sharpe"] >= 1.0 else bad).append(f"Sharpe {m['sharpe']:.2f}")
    (good if fee_est / cap < 0.01 else bad).append(
        f"수수료 추정 {fee_est:,.0f} (원금의 {fee_est / cap:.1%})")
    if turnover > 3:
        bad.append(f"회전율 {turnover:.1f}배 — 리밸런싱·RSI 발동 과다 의심")
    if fwd_sell is not None and fwd_sell > 0.03:
        bad.append(f"RSI 매도 후 20일 평균 {fwd_sell:+.1%} — 매도가 이른 편")
    if fwd_buy is not None and fwd_buy < -0.03:
        bad.append(f"RSI 매수 후 20일 평균 {fwd_buy:+.1%} — 하락 지속 구간 매수")
    if avg_w:
        t = next(iter(avg_w))
        if avg_w[t] > 0.25:
            bad.append(f"{t.removesuffix('_w')} 평균 비중 {avg_w[t]:.0%} — 쏠림")
    if len(mo) and neg_m >= len(mo) / 2:
        bad.append(f"음수 월 {neg_m}/{len(mo)} — 상승장 대응 약함")
    if rec_days is None and m["MDD"] < -0.10:
        bad.append("전고 미회복 — 드로다운 장기화")
    if excess < 0 and top_bh[0]:
        bad.append(f"B&H는 {top_bh[0]}({top_bh[1]:.0%}) 주도 — 주도주 편입 부족")
    if best[0]:
        good.append(f"최고 월 {best[0]} {best[1]:+.1%} / 최악 월 {worst[0]} {worst[1]:+.1%}")

    lines = ["[좋았던 점]"]
    lines += [f"- {g}" for g in good] or ["- (두드러진 강점 없음)"]
    lines += ["[나빴던 점 / 원인 가설]"]
    lines += [f"- {b}" for b in bad] or ["- (두드러진 약점 없음)"]
    lines += ["[비용·회전율 진단]"]
    grp = trades["reason"].str.replace(r"\(.*$", "", regex=True).value_counts() \
        if len(trades) else {}
    top_reasons = ", ".join(f"{k} {v}" for k, v in
                            sorted(grp.items(), key=lambda x: -x[1])[:4]) or "없음"
    lines.append(f"- 총 거래 {len(trades)}건 ({top_reasons})")
    lines.append(f"- 회전율 {turnover:.2f}배, 수수료 제외 시 총수익률 {fee_free:.1%}")
    lines.append("- 스냅샷 펀더멘털의 사후편향 한계: 제출 전 FY2023 확정치로 교체 검토")
    return {"facts": facts, "lines": lines}

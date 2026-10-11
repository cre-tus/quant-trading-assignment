"""거래이력 한눈보기 (trade_log.csv -> trade_history_view.csv).

거래 한 건마다 체결 정보 + 실현손익 + 거래 후 자산 상태를 한 행에 정리한다.
한글 헤더·UTF-8 BOM으로 엑셀에서 바로 열린다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.names import load_names, name_of

REASON_KR = [
    ("SHORT_STOP", "손절매"),
    ("SHORT_SELL", "단기매도(RSI)"),
    ("SHORT_BUY", "단기매수(RSI)"),
    ("REBALANCE", "리밸런싱"),
    ("INIT", "최초편입"),
    ("EXEMPT", "보유유지(H&S)"),
]

TYPE_KR = {"BUY": "매수", "SELL": "매도"}

COLUMNS = ["순번", "날짜", "구분", "종목", "종목명", "수량", "체결가", "거래금액",
           "수수료", "사유", "실현손익", "실현수익률%", "종목누적실현손익",
           "보유일수", "거래후현금", "거래후총자산", "거래후누적수익률%"]


def reason_kr(reason: str) -> str:
    r = str(reason)
    for prefix, label in REASON_KR:
        if r.startswith(prefix):
            return label
    return r


def build_trade_view(outdir: str | Path, fee_rate: float = 0.001,
                     names: dict | None = None) -> Path:
    """거래이력 뷰 CSV를 만들고 경로를 반환한다."""
    odir = Path(outdir)
    trades = pd.read_csv(odir / "trade_log.csv", parse_dates=["date"])
    equity = pd.read_csv(odir / "daily_equity.csv", index_col=0, parse_dates=True)
    if names is None:
        try:
            names = load_names()
        except Exception:
            names = {}
    base = float(equity["total"].iloc[0])

    eq = equity[["total", "cash"]]
    rows = []
    cum_pnl: dict[str, float] = {}
    last_buy: dict[str, pd.Timestamp] = {}
    for i, t in trades.reset_index(drop=True).iterrows():
        ticker = str(t["ticker"])
        is_sell = str(t["type"]).upper() == "SELL"
        pnl = float(t.get("pnl", 0.0) or 0.0)
        cum_pnl[ticker] = cum_pnl.get(ticker, 0.0) + pnl
        if not is_sell:
            last_buy[ticker] = pd.Timestamp(t["date"])
            held = float("nan")
        elif ticker in last_buy:
            held = float((pd.Timestamp(t["date"]) - last_buy[ticker]).days)
        else:
            held = float("nan")
        hist = eq.loc[eq.index <= pd.Timestamp(t["date"])]
        snap = hist.iloc[-1] if len(hist) else eq.iloc[0]
        total = float(snap["total"])
        rows.append({
            "순번": int(i) + 1,
            "날짜": pd.Timestamp(t["date"]).strftime("%Y-%m-%d"),
            "구분": TYPE_KR.get(str(t["type"]).upper(), str(t["type"])),
            "종목": ticker,
            "종목명": name_of(ticker, names),
            "수량": round(float(t["qty"]), 4),
            "체결가": round(float(t["price"]), 4),
            "거래금액": round(float(t["amount"]), 0),
            "수수료": round(float(t["amount"]) * fee_rate, 0),
            "사유": reason_kr(t.get("reason", "")),
            "실현손익": round(pnl, 0) if is_sell else 0,
            "실현수익률%": round(float(t.get("ret", 0.0) or 0.0) * 100, 2) if is_sell else 0.0,
            "종목누적실현손익": round(cum_pnl[ticker], 0),
            "보유일수": held,
            "거래후현금": round(float(snap["cash"]), 0),
            "거래후총자산": round(total, 0),
            "거래후누적수익률%": round((total / base - 1) * 100, 2),
        })
    view = pd.DataFrame(rows, columns=COLUMNS)
    out = odir / "trade_history_view.csv"
    view.to_csv(out, index=False, encoding="utf-8-sig")
    return out


if __name__ == "__main__":
    import sys

    import yaml

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs")
    fee = 0.001
    try:
        fee = float(yaml.safe_load(
            Path("config.yaml").read_text(encoding="utf-8"))["costs"]["fee_rate"])
    except Exception:
        pass
    print(build_trade_view(target, fee))

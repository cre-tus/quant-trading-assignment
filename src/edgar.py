"""EDGAR companyfacts 기반 스냅샷 펀더멘털 (무료·무키, point-in-time).

filed ≤ design_cutoff 인 최신 10-K만 사용한다. 12월 결산사는 FY2023 10-K가
2024년에 공시되므로 FY2022 값이 들어간다 — 컷오프 시점에 알 수 있던 값만
쓰기 위한 정확한 동작이다. 회사별 JSON은 data/edgar_cache에 캐시된다.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

UA = {"User-Agent": "UniBacktest research contact@univ.edu"}
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

EPS_TAGS = ["EarningsPerShareDiluted", "EarningsPerShareBasic"]
EQ_TAGS = ["StockholdersEquity",
           "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
SH_TAGS = ["WeightedAverageNumberOfDilutedSharesOutstanding",
           "WeightedAverageNumberOfSharesOutstandingBasic"]


def fetch_facts(cik, cache_dir: str = "data/edgar_cache",
                delay: float = 0.15) -> dict:
    p = Path(cache_dir) / f"{int(cik):010d}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    req = urllib.request.Request(FACTS_URL.format(cik=int(cik)), headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=60))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d), encoding="utf-8")
    time.sleep(delay)  # SEC 권장 예의 (초당 10건 이하)
    return d


def _fy_value(facts: dict, tags: list[str], cutoff: str):
    """filed ≤ cutoff 최신 10-K 값. 없으면 None."""
    best = None
    for tag in tags:
        node = (facts.get("facts", {}).get("us-gaap", {}).get(tag) or {})
        for pts in node.get("units", {}).values():
            for x in pts:
                if x.get("form") != "10-K":
                    continue
                if str(x.get("filed", "")) > cutoff:
                    continue
                key = (x.get("fy", 0), str(x.get("filed", "")))
                if best is None or key > best[0]:
                    best = (key, x.get("val"))
        if best is not None:
            break
    return best[1] if best is not None else None


def fy_snapshot(tickers: list[str], cik_of: dict, price0: pd.Series,
                cutoff: str = "2023-12-31", cache_dir: str = "data/edgar_cache",
                log_every: int = 200) -> pd.DataFrame:
    """티커별 trailingPE·PBR (2023년 말 종가 기준). 결측은 NaN(최하위 취급)."""
    rows = {}
    for i, t in enumerate(tickers):
        try:
            facts = fetch_facts(cik_of[t], cache_dir)
            eps = _fy_value(facts, EPS_TAGS, cutoff)
            eq = _fy_value(facts, EQ_TAGS, cutoff)
            sh = _fy_value(facts, SH_TAGS, cutoff)
            bps = eq / sh if eq and sh else None
            p0 = float(price0.get(t, float("nan")))
            rows[t] = {
                "trailingPE": p0 / eps if eps and eps > 0 else None,
                "priceToBook": p0 / bps if bps and bps > 0 else None,
            }
        except Exception:
            rows[t] = {"trailingPE": None, "priceToBook": None}
        if log_every and (i + 1) % log_every == 0:
            print(f"[edgar] {i + 1}/{len(tickers)}")
    return pd.DataFrame(rows).T.apply(pd.to_numeric, errors="coerce")

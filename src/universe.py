"""전종목 유니버스 (SEC EDGAR 상장 목록, 무료·무키).

company_tickers.json = 티커·CIK·종목명 전체 (펀더멘털 수집용 CIK 매핑 겸용).
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

UA = {"User-Agent": "UniBacktest research contact@univ.edu"}
EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# 보통주가 아닌 것 제거용 (이름 기준). REIT 중 Trust 포함 종목도 제외된다.
DROP_TITLE = ("WARRANT", "UNIT", "RIGHTS", "PREFERRED", " ETF", "ETF ",
              "ETN", "TRUST", "FUND", "ROYALTY", "PARTNERS")


def fetch_all_listings(cache: str = "data/edgar_tickers.csv",
                       offline: bool = False) -> tuple[pd.DataFrame, str]:
    cp = Path(cache)
    if offline:
        if cp.exists():
            return pd.read_csv(cp), "edgar cache"
        raise ValueError("오프라인인데 상장 캐시 없음")
    try:
        req = urllib.request.Request(EDGAR_TICKERS_URL, headers=UA)
        d = json.load(urllib.request.urlopen(req, timeout=60))
        df = pd.DataFrame(list(d.values()))
        cp.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cp, index=False)
        return df, "edgar live"
    except Exception as e:
        if cp.exists():
            return pd.read_csv(cp), "edgar cache"
        raise ValueError(f"상장 목록 실패, 캐시 없음: {e}")


def fetch_nasdaq_listed(cache: str = "data/nasdaq_listed.csv",
                        offline: bool = False) -> tuple[pd.DataFrame, str]:
    """나스닥 공식 상장 파일 (테스트종목·ETF 제외한 거래소 상장 보통주).
    OTC가 섞인 EDGAR 목록과 달리 야후 시세가 있는 종목만 남는다."""
    cp = Path(cache)
    if offline:
        if cp.exists():
            return pd.read_csv(cp), "nasdaq cache"
        raise ValueError("오프라인인데 나스닥 캐시 없음")
    try:
        rows = []
        for url, sep_t in (("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", "NASDAQ"),
                           ("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt", "OTHER")):
            req = urllib.request.Request(url, headers=UA)
            text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
            lines = [ln for ln in text.splitlines()
                     if ln and not ln.startswith("File Creation Time")]
            rows += _parse_nasdaq(lines, sep_t)
        df = pd.DataFrame(rows).drop_duplicates("ticker").reset_index(drop=True)
        cp.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cp, index=False)
        return df, "nasdaq live"
    except Exception as e:
        if cp.exists():
            return pd.read_csv(cp), "nasdaq cache"
        raise ValueError(f"나스닥 목록 실패, 캐시 없음: {e}")


def _parse_nasdaq(lines: list, kind: str) -> list:
    """나스닥 상장 파일 파싱 (테스트종목·ETF 제외)."""
    rows = []
    if kind == "NASDAQ":
        for ln in lines[1:]:
            p = ln.split("|")
            if len(p) < 7 or p[3] == "Y" or p[6] == "Y":
                continue
            rows.append({"ticker": p[0].strip(), "name": p[1].strip(),
                         "exchange": "NASDAQ"})
    else:
        for ln in lines[1:]:
            p = ln.split("|")
            if len(p) < 7 or p[6] == "Y" or p[4] == "Y":
                continue
            rows.append({"ticker": (p[7].strip() or p[0].strip()),
                         "name": p[1].strip(), "exchange": p[2].strip()})
    return rows


def filter_common(df: pd.DataFrame) -> pd.DataFrame:
    """보통주 후보만: 특수문자 티커·워런트·ETF·신탁 등 제외."""
    t = df["ticker"].astype(str).str.upper()
    keep_t = ~t.str.contains(r"[^A-Z]", regex=True)
    keep_t &= ~(t.str.len().eq(5) & t.str.endswith(("W", "U", "R")))  # 5번째 문자 관례
    up = df["title"].astype(str).str.upper()
    keep_n = ~up.apply(lambda s: any(k in s for k in DROP_TITLE))
    return df[keep_t & keep_n].reset_index(drop=True)

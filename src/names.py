"""티커 → 한국어 종목명 (data/stock_names_kr.csv).

전종목 한글 매핑은 무료 소스가 없으므로, 파일에 있는 종목만 한글 표시하고
없는 티커는 영문명(yfinance longName)이나 티커 그대로 둔다.
모르는 종목이 나오면 CSV에 한 줄 추가하면 된다.
"""
from __future__ import annotations

from pathlib import Path

DEFAULT_PATH = "data/stock_names_kr.csv"


def load_names(path: str = DEFAULT_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines()[1:]:
        parts = [x.strip() for x in line.split(",", 1)]
        if len(parts) == 2 and parts[0]:
            out[parts[0].upper()] = parts[1]
    return out


def name_of(ticker: str, names: dict | None = None, fallback: str = "") -> str:
    t = ticker.upper()
    if names and t in names:
        return names[t]
    return fallback or t

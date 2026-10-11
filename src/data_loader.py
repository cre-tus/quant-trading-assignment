"""가격/펀더멘털 데이터 수집.

온라인(yfinance) 우선, 실패 시 오프라인 합성데이터로 폴백한다.
합성데이터는 재현 가능하도록 시드 고정(데모/검증용)이며,
실제 제출용 백테스트는 온라인 데이터로 실행해야 한다.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd


def _synthetic_prices(tickers: list[str], start: str, end: str, seed: int = 42) -> pd.DataFrame:
    dates = pd.bdate_range(start, end)
    rng = np.random.default_rng(seed)
    base = {t: 50 + (abs(hash(t)) % 400) for t in tickers}
    drifts = {t: 0.0002 + (rng.random() - 0.5) * 0.001 for t in tickers}
    vols = {t: 0.015 + rng.random() * 0.01 for t in tickers}
    data = {}
    for t in tickers:
        rets = rng.normal(drifts[t], vols[t], len(dates))
        data[t] = base[t] * np.exp(np.cumsum(rets))
    return pd.DataFrame(data, index=dates)


def _synthetic_fundamentals(tickers: list[str], seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "trailingPE": rng.uniform(8, 45, len(tickers)).round(2),
            "priceToBook": rng.uniform(1, 15, len(tickers)).round(2),
        },
        index=tickers,
    )


def _dl_one_tv(args) -> tuple:
    """단일 티커 종가+거래량. (t, close, vol) 또는 예외."""
    t, start, end = args
    import yfinance as yf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = yf.download(t, start=start, end=end, auto_adjust=True,
                         progress=False)
    if df is None or df.empty:
        raise ValueError("empty")
    c = df["Close"]
    if isinstance(c, pd.DataFrame):
        c = c.iloc[:, 0]
    v = df["Volume"] if "Volume" in df else pd.Series(float("nan"), index=df.index)
    if isinstance(v, pd.DataFrame):
        v = v.iloc[:, 0]
    c = c.dropna()
    v = v.reindex(c.index)
    if len(c) < 50:
        raise ValueError(f"too short ({len(c)})")
    return t, c, v


def merge_frames(old: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """부분 수집 병합 (중복 열은 기존 우선, 인덱스 정렬)."""
    if old is None or not len(old.columns):
        return new.sort_index()
    merged = pd.concat([old, new], axis=1)
    merged = merged.loc[:, ~merged.columns.duplicated(keep="first")]
    return merged.sort_index()


def load_market_data(tickers: list[str], start: str, end: str,
                     workers: int = 8, offline: bool = False,
                     return_failed: bool = False
                     ) -> tuple:
    """(종가DF, 거래량DF, 출처[, 실패목록]). 전종목도 스레드 병렬로 수집."""
    if offline:
        out = (_synthetic_prices(tickers, start, end), None, "synthetic(offline demo)")
        return (*out, []) if return_failed else out
    from concurrent.futures import ThreadPoolExecutor, as_completed
    closes, vols, failed = {}, {}, []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_dl_one_tv, (t, start, end)): t for t in tickers}
        done = 0
        for fut in as_completed(futs):
            t = futs[fut]
            try:
                _, c, v = fut.result()
                closes[t], vols[t] = c, v
            except Exception:
                failed.append(t)
            done += 1
            if done % 500 == 0:
                print(f"[data] {done}/{len(tickers)} 수집 (성공 {len(closes)})")
    if failed:
        print(f"[data] 실패 {len(failed)}종목 제외 (예: {', '.join(failed[:10])})")
    close = pd.DataFrame(closes).sort_index().ffill().dropna(how="all")
    vol = pd.DataFrame(vols).reindex(close.index) if vols else None
    if close.empty or len(close) < 50 or close.shape[1] == 0:
        raise ValueError("downloaded price history too short/sparse")
    if return_failed:
        return close, vol, "yfinance", failed
    return close, vol, "yfinance"


def load_prices(tickers: list[str], start: str, end: str,
                cache_dir: str = "data", offline: bool = False) -> tuple[pd.DataFrame, str]:
    """(가격DF, 출처문자열) 반환. 출처는 'yfinance' 또는 'synthetic(offline demo)'."""
    if offline:
        return _synthetic_prices(tickers, start, end), "synthetic(offline demo)"
    try:
        close, _, src = load_market_data(tickers, start, end, offline=False)
        if close.shape[1] < max(5, len(tickers) // 2):
            print(f"[data] 수신 {close.shape[1]}/{len(tickers)}종목 — 유동성 필터에서 정리")
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        close.to_csv(Path(cache_dir) / "prices.csv")
        return close, src
    except Exception as e:  # 네트워크/파싱 실패 시 폴백
        print(f"[data] yfinance 실패({e}) → 합성 데모데이터로 폴백")
        return _synthetic_prices(tickers, start, end), "synthetic(offline demo)"


def filter_liquid(close: pd.DataFrame, vol: pd.DataFrame | None, cutoff: str,
                  min_dollar_vol: float = 1_000_000, lookback: int = 60) -> tuple[list, dict]:
    """컷오프 이전 lookback일 평균 일대금 하한 필터. (P0: 컷오프 이전 데이터만)"""
    if vol is None:
        return list(close.columns), {"universe": int(close.shape[1]),
                                     "liquid": int(close.shape[1]), "note": "no volume (demo)"}
    win = vol.loc[vol.index <= pd.Timestamp(cutoff)].tail(lookback)
    dvol = (close.reindex(win.index) * win).mean()
    kept = dvol[dvol >= min_dollar_vol].index.tolist()
    return kept, {"universe": int(close.shape[1]), "liquid": len(kept),
                  "min_dollar_vol": min_dollar_vol, "lookback": lookback}


MANUAL_FUND = "data/fundamentals_fy2023.csv"


def load_universe(path: str) -> list[str]:
    """유니버스 파일(한 줄 한 티커, # 주석) 로드. 대문자·중복제거."""
    tickers = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip().upper()
        if line and not line.startswith("#") and line not in tickers:
            tickers.append(line)
    if not tickers:
        raise ValueError(f"비어 있는 유니버스 파일: {path}")
    return tickers


def load_fundamentals(tickers: list[str], offline: bool = False,
                      manual_path: str = MANUAL_FUND,
                      write_cache: bool = True) -> tuple[pd.DataFrame, str]:
    """과제 옵션1용 스냅샷 펀더멘털(trailingPE, PBR). 반환: (DF, 출처).

    우선순위: 수동 FY2023 파일(design_cutoff 이전 확정치) > yfinance 현재값.
    yfinance 현재값은 미래 정보가 섞인 스냅샷이므로 출처에 LOOKAHEAD-RISK를
    명시한다. 제출 전에는 수동 파일에 FY2023 확정치를 채워야 한다.
    """
    if offline:
        return _synthetic_fundamentals(tickers), "synthetic(offline demo)"
    base = None
    mp = Path(manual_path)
    if mp.exists():
        try:
            base = pd.read_csv(mp, index_col=0, comment="#")
            base = base.apply(pd.to_numeric, errors="coerce")
        except Exception as e:
            print(f"[data] 수동 펀더멘털 읽기 실패({e}) → yfinance로 진행")
            base = None
    cols = ["trailingPE", "priceToBook"]
    # 스냅샷 캐시: 지난 실행에서 받은 yfinance 값을 재사용해 대량 유니버스도 감당.
    cache = None
    cp = Path("data/fundamentals_snapshot.csv")
    if cp.exists():
        try:
            cache = pd.read_csv(cp, index_col=0, comment="#")
            cache = cache.apply(pd.to_numeric, errors="coerce")
        except Exception:
            cache = None

    def manual_covered(t: str) -> bool:
        return base is not None and t in base.index and base.loc[t, cols].notna().all()

    def cache_row(t: str) -> dict | None:
        if cache is not None and t in cache.index:
            r = cache.loc[t, cols]
            if r.notna().all() and bool((r != 999.0).all()):
                return {c: float(r[c]) for c in cols}
        return None

    need = [t for t in tickers if not manual_covered(t) and cache_row(t) is None]
    filled: dict = {}
    if need:
        try:
            import yfinance as yf
            for t in need:
                info = yf.Ticker(t).info or {}
                filled[t] = {"trailingPE": info.get("trailingPE"),
                             "priceToBook": info.get("priceToBook")}
        except Exception as e:
            print(f"[data] fundamentals 실패({e}) → 합성 데모데이터로 폴백")
            return _synthetic_fundamentals(tickers), "synthetic(offline demo)"
    rows = {}
    for t in tickers:
        if manual_covered(t):
            rows[t] = {c: float(base.loc[t, c]) for c in cols}
        elif (cr := cache_row(t)) is not None:
            rows[t] = cr
        elif t in filled:
            rows[t] = filled[t]
        else:
            rows[t] = {"trailingPE": None, "priceToBook": None}
    df = pd.DataFrame(rows).T.apply(pd.to_numeric, errors="coerce")
    if df["trailingPE"].isna().all():
        print("[data] 펀더멘털 전멸 → 합성 데모데이터로 폴백")
        return _synthetic_fundamentals(tickers), "synthetic(offline demo)"
    # 결측은 해당 지표 최하위 취급을 위해 큰 값으로 채움(기록용)
    df = df.fillna(999.0)
    if write_cache:
        Path("data").mkdir(parents=True, exist_ok=True)
        df.to_csv("data/fundamentals_snapshot.csv")
    n_manual = sum(1 for t in tickers if manual_covered(t))
    n_cache = sum(1 for t in tickers
                  if not manual_covered(t) and cache_row(t) is not None)
    parts = []
    if n_manual:
        parts.append(f"manual FY2023({n_manual})")
    if n_cache:
        parts.append(f"cache({n_cache})")
    if need:
        parts.append(f"yfinance snapshot({len(need)})")
    src = " + ".join(parts) if parts else "empty"
    if n_manual == len(tickers):
        src += " (point-in-time)"
    else:
        src += " (LOOKAHEAD-RISK: 제출 전 FY2023 확정치로 교체)"
    return df, src

"""전종목 풀 구축 1단계: 상장→보통주→시세→유동성 필터. 산출물: data/pool.json.

사용법: python tools/build_pool.py [--warmup 2023-10-01] [--end 2025-12-31]
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import filter_liquid, load_market_data
from src.universe import fetch_all_listings, fetch_nasdaq_listed, filter_common


def main() -> None:
    warmup = sys.argv[sys.argv.index("--warmup") + 1] if "--warmup" in sys.argv else "2023-10-01"
    end = sys.argv[sys.argv.index("--end") + 1] if "--end" in sys.argv else "2025-12-31"
    cutoff = sys.argv[sys.argv.index("--cutoff") + 1] if "--cutoff" in sys.argv else "2023-12-31"
    source = sys.argv[sys.argv.index("--source") + 1] if "--source" in sys.argv else "nasdaq"
    if source == "nasdaq":
        df_list, list_src = fetch_nasdaq_listed()
        t = df_list["ticker"].astype(str).str.upper()
        keep = ~t.str.contains(r"[^A-Z]", regex=True)
        keep &= ~(t.str.len().eq(5) & t.str.endswith(("W", "U", "R")))
        df_list = df_list[keep].reset_index(drop=True)
        tickers = df_list["ticker"].tolist()
        try:  # EDGAR 펀더멘털용 CIK 매핑 저장
            import pandas as pd
            ed = pd.read_csv("data/edgar_tickers.csv")
            cmap = dict(zip(ed["ticker"].astype(str).str.upper(), ed["cik_str"]))
            Path("data/pool_cik.json").write_text(json.dumps(
                {t: int(cmap[t]) for t in tickers if t in cmap}),
                encoding="utf-8")
        except Exception as e:
            print(f"[pool] CIK 매핑 생략({e})")
    else:
        df_list, list_src = fetch_all_listings()
        df_list = filter_common(df_list)
        tickers = df_list["ticker"].tolist()
    print(f"[pool] 상장 {len(df_list)} ({list_src}) → 수집 시작", flush=True)
    import time
    from src.data_loader import merge_frames
    part_p = Path("data/prices_part.csv")
    part_v = Path("data/volumes_part.csv")
    fail_p = Path("data/pool_failed.txt")
    close_acc, vol_acc, bad = None, None, set()
    if part_p.exists():  # 중단 시 이어받기
        try:
            close_acc = pd.read_csv(part_p, index_col=0, parse_dates=True)
            if part_v.exists():
                vol_acc = pd.read_csv(part_v, index_col=0, parse_dates=True)
            print(f"[pool] 체크포인트 이어받음 ({close_acc.shape[1]}종목)", flush=True)
        except Exception as e:
            print(f"[pool] 체크포인트 무시({e})", flush=True)
            close_acc, vol_acc = None, None
    if fail_p.exists():
        bad = set(fail_p.read_text(encoding="utf-8").splitlines())
    done = set(close_acc.columns) if close_acc is not None else set()
    todo = [t for t in tickers if t not in done and t not in bad]
    CHUNK = 500
    for i in range(0, len(todo), CHUNK):
        grp = todo[i:i + CHUNK]
        try:
            c, v, _, failed = load_market_data(grp, warmup, end, return_failed=True)
        except ValueError:
            continue  # 청크 전멸 → 재시도 패스에서 처리
        close_acc = merge_frames(close_acc, c)
        if v is not None:
            vol_acc = merge_frames(vol_acc, v)
        bad.update(f for f in failed if f not in close_acc.columns)
        close_acc.to_csv(part_p)
        if vol_acc is not None:
            vol_acc.to_csv(part_v)
        fail_p.write_text("\n".join(sorted(bad)), encoding="utf-8")
        print(f"[pool] {min(i + CHUNK, len(todo))}/{len(todo)} "
              f"(누적 {close_acc.shape[1]})", flush=True)
    close, vol = close_acc, vol_acc
    if close is None or not len(close.columns):
        raise ValueError("수집 전멸 — 네트워크/제한 확인 후 재실행")
    missing = [t for t in tickers
               if t not in close.columns and t not in bad]
    if missing:  # 제한으로 탈락한 종목 재시도 (천천히)
        print(f"[pool] 재시도 {len(missing)}종목 (60초 대기 후)", flush=True)
        time.sleep(60)
        try:
            close2, vol2, _, _ = load_market_data(missing, warmup, end,
                                                  workers=2, return_failed=True)
            close = merge_frames(close, close2)
            if vol2 is not None:
                vol = merge_frames(vol, vol2)
            print(f"[pool] 재시도 후 {close.shape[1]}종목", flush=True)
        except ValueError:
            print("[pool] 재시도 전멸 — 다음 실행에서 계속", flush=True)
    close.to_csv("data/prices_full.csv")
    if vol is not None:
        vol.to_csv("data/volumes_full.csv")
    kept, liq = filter_liquid(close, vol, cutoff)
    pool = {"source": list_src, "listed": len(tickers),
            "downloaded": int(close.shape[1]), "liquid": kept,
            "liquid_n": len(kept), "filter": liq}
    Path("data/pool.json").write_text(json.dumps(
        {k: v for k, v in pool.items() if k != "liquid"}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    Path("data/pool_tickers.txt").write_text("\n".join(kept), encoding="utf-8")
    print(f"[pool] 수신 {close.shape[1]} → 유동성 {len(kept)}종목", flush=True)


if __name__ == "__main__":
    main()

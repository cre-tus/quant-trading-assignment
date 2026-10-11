"""기존 discovery.csv에 name_kr 열 추가 (일회성 보정)."""
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.names import load_names

names = load_names()
for p in sorted(glob.glob("outputs*/discovery.csv")):
    df = pd.read_csv(p)
    if "name_kr" not in df.columns:
        df.insert(1, "name_kr", df["ticker"].map(lambda t: names.get(t, t)))
        df.to_csv(p, index=False)
    print(p, "rows:", len(df), "has name_kr:", "name_kr" in df.columns)

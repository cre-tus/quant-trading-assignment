"""기존 산출물 폴더에 report.xlsx 생성. 사용법: python make_excel.py outputs [...]"""
from __future__ import annotations

import sys

from src.excel_report import build_workbook


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python make_excel.py <outdir> [...]")
        raise SystemExit(2)
    for d in sys.argv[1:]:
        try:
            print(f"{d} → {build_workbook(d)}")
        except Exception as e:
            print(f"{d} 실패: {e}")


if __name__ == "__main__":
    main()

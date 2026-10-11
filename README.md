# 리밸런싱 백테스트 실험 환경 (2024–2025)

전략은 직접 작성하고, 데이터·엔진·지표·리포트는 이 환경이 담당한다.

## 환경

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## 본인 전략 작성 (핵심 2단계)

1. [src/strategies/my_strategy.py](src/strategies/my_strategy.py)의
   `targets`(목표비중 dict)와 `tactical`(일중 주문 리스트)을 채운다.
2. [config.yaml](config.yaml)의 `strategy.module`을 `"my_strategy"`로 바꾼다.

참고용 예시(`example_value_rsi`, 테스트용)는 건드리지 말 것.

## 실행

```powershell
python run_backtest.py            # yfinance 온라인 시도
python run_backtest.py --offline  # 합성 데모데이터(인터넷 불필요)
python run_backtest.py --freq 2W  # 주기 오버라이드: 1W|2W|4W|M|Q
python -m unittest discover -s tests  # 회귀테스트
```

## 산출물 (outputs/)

trade_log.csv, holdings_snapshots.csv, daily_holdings.csv(매일 보유·평단·수익률),
discovery.csv(종목별 손익표), daily_equity.csv, metrics.json,
analysis.json·analysis.md(결과 분석·평가 자동 생성),
equity_curve.png, report.pptx, report.xlsx(날짜 #### 방지 서식)가 자동 생성된다.
기존 폴더만 엑셀로 바꾸려면 `python make_excel.py <폴더>`를 쓴다.
기존 예시 실행 기록은 [outputs_demo](outputs_demo/README_테스트기록.md)에
테스트용으로 보관되어 있다.

## 시간 기준선 (필수)

- 전략 설계는 2023-12-31까지 데이터만, 2024~2025는 평가 전용(뒷북 금지).
- 상세 지침은 [prompts/AI프롬프트모음.md](prompts/AI프롬프트모음.md) P0.

## 한계 (제출 전 확인)

- yfinance 펀더멘털은 스냅샷이라 엄밀한 point-in-time DB가 아니다.
  `data/fundamentals_fy2023.csv`에 FY2023 확정치를 채워 교체할 것.
- 미국 편도 수수료 0.1% 가정, 세금 0.

# AI 프롬프트 모음 (제출물 2-1: 코드 혹은 AI 프롬프트)

> 기록 원칙: 이 파일에는 **시스템 반영과 전략 결정을 함께** 기록한다.
> P번호는 시스템(엔진·데이터·산출물) 반영, S번호는 전략(규칙·수치·근거) 기록이다.
> 전략은 본인이 직접 수정해나가는 영역이므로, 바꿀 때마다 해당 S항목을 갱신한다.
> 전략 코드는 `src/strategies/my_strategy.py`에, 결정 내용과 근거는 여기에 적는다.

## P0. 시간 기준선 지침 [시스템 반영됨]

> 백테스팅 기간은 2024.1.1~2025.12.31이며, 초기 전략은 그 이전인
> **2023-12-31까지의 데이터셋만 보고** 정한다. 그 이후 구간은 전부 미래(표본외)다.
>
> 1. 설계 데이터: 2023-12-31 이전만 사용. 펀더멘털은 FY2023 확정치
>    (`data/fundamentals_fy2023.csv`에 기입, 2023 annual report/10-K 기준).
>    상태: 수동 파일이 비어 있어 K안은 EDGAR 확정치만 사용(manual 0). 제출 전 기입 필요.
> 2. 뒷북 금지: 2024~2025 구간 수익률을 보고 유니버스·종목·파라미터를
>    고르거나 바꾸지 않는다. 이 구간은 오직 평가용이다.
> 3. 웜업 예외: 2023-10~12 가격은 지표 시동용으로만 쓰고 매매·판단에 쓰지 않는다.
> 4. 엔진은 당일까지의 데이터만 본다. 전략 코드에 미래 참조가 있으면 버그로 취급한다.
> 5. yfinance 현재값 펀더멘털을 쓴 경우 출처에 LOOKAHEAD-RISK를 남긴다.
>
> 반영 위치: `config.yaml`(design_cutoff, warmup_start), `src/backtest.py`(start
> 이전 매매 차단), `src/data_loader.py`(수동 FY2023 우선 + LOOKAHEAD-RISK 표기).

## P1. 시스템 골격 생성 [시스템 반영됨 — 전략 수치는 예시로 격리]

> config.yaml 기반 Python 백테스트 엔진 + 산출물(trade_log.csv,
> holdings_snapshots.csv, daily_equity.csv, metrics.json, equity_curve.png,
> report.pptx 자동생성) 구조로 만들어줘.
>
> 반영 위치: `run_backtest.py`, `src/` 엔진·지표·리포트, `config.yaml`.
> 단, 프롬프트에 있던 전략 수치(옵션1 규칙, RSI 85/20 등)는
> `src/strategies/example_value_rsi.py` 테스트용 예시로 격리했고 본 전략이 아니다.

## P2. 동적 랭킹의 look-ahead 제거 [시스템 반영됨]

> 스냅샷 EPS0/BPS0 + 당일 가격으로 동적 랭킹(PER_t=P_t/EPS0)을 계산해
> 신규 정보 유입 없이 순위가 변하게 구현하고, 한계는 PPT에 명시해줘.
>
> 반영 위치: `src/factors.py`, `src/report.py` 한계 슬라이드.
> 스냅샷 출처 규칙은 P0의 수동 FY2023 방식으로 통합됐다.

## P3. 결과 분석 슬라이드 자동생성 [시스템 반영됨]

> metrics.json을 읽고 좋았던 점 / 나빴던 점과 원인 가설을 bullet으로 정리해
> PPT '결과 분석 및 평가' 슬라이드에 넣어줘.
>
> 반영 위치: `src/report.py`. 문구는 예시 전략 기준 초안이므로 본 전략 결과에
> 맞게 직접 고쳐 쓴다.

## P4. 결과 분석·평가 자동화 [시스템 반영됨]

> 지표·거래·스냅샷·가격만으로 원인 진단(회전율·수수료 추정, RSI 매매 후 20일
> 수익률, 편입 빈도·쏠림, 최고/최악 월, 전고 회복일, B&H 주도주 비교)까지 뽑아
> analysis.json·analysis.md로 저장하고 PPT '결과 분석 및 평가' 슬라이드에 넣어줘.
> 전략 로직에 종속되지 않게 할 것.
>
> 반영 위치: `src/analysis.py`, `run_backtest.py`, `src/report.py`(analysis_lines).

## P5. 외부 지표 선별 도입 [시스템 반영됨]

> 깃헙 스타 상위 퀀트 지표 라이브러리를 조사하고, 여러 지표를 지원하는 것 중
> 일부만 가져다 쓴다. 자작 계산이 제출 기준값으로 남고, 라이브러리는 교차검증용이다.
>
> 반영 위치: `requirements.txt`(empyrical-reloaded), `src/metrics.py`
> (CROSS_CHECK_METRICS 5종: annual_return, max_drawdown, sharpe_ratio,
> sortino_ratio, calmar_ratio), `run_backtest.py`(metrics.json cross_check 기록).

## P6. 전략 선정형 유니버스 [풀 이전 — 기록만 유지]

> 60종목 파일(`data/universe_us.txt`) 선정 방식. K안은 P7 풀 파이프라인 사용.
> 파일 모드(`--universe file`)는 코드에 연기·테스트용으로만 남고 전략 근거가 아니다.

## P7. 전종목 파이프라인 [시스템 반영됨]

> EDGAR 상장 목록(10,445개, 무료·무키)으로 전종목 수집. 보통주 필터 +
> 유동성 필터(컷오프 이전 데이터만)로 거래 가능 종목만 남기고, 펀더멘털은
> EDGAR companyfacts 확정치(filed≤컷오프, 회사별 JSON 캐시)로 계산한다.
> 대량 수집은 스레드 병렬 + 실패 종목 제외. 리포트 펀드 슬라이드는 25개로 축소.
>
> 반영 위치: `src/universe.py`, `src/edgar.py`, `src/data_loader.py`
> (load_market_data, filter_liquid), `run_backtest.py`
> (--universe, --max-tickers, fund_mode 분기), `config.yaml`
> (universe_source, fund_mode, min_dollar_vol), `src/report.py`.

## P8. 실험/본선 2단계 모드 [시스템 반영됨]

> 2023년 실험(experiment: 설계 ≤2022-12-31, 산출물 outputs_exp)에서 전략을
> 개발·튜닝하고, 통과하면 2024~2025 본 백테스트(final)로 넘어간다.
> 모드별 warmup·컷오프·산출 폴더가 섞이지 않게 기간 해석을 한 곳에 모았다.
>
> 반영 위치: `src/strategy.py`(resolve_period), `run_backtest.py`
> (--mode, --outdir), `config.yaml`(mode).

## P10. 일별 보유·종목 손익 리포트 [시스템 반영됨]

> 장이 열린 날마다 전 종목 보유·평단·수익률을 daily_holdings.csv에,
> 종목별 매수·매도·실현·미실현·합계 손익을 discovery.csv에 정리.
> 매도 거래에 실현손익(pnl/ret) 기록. 초기 시드 10억.
>
> 반영 위치: `src/backtest.py`(평단·실현손익·일별 기록),
> `src/discovery.py`, `run_backtest.py`(저장·종목손익 출력),
> `config.yaml`(initial_capital).

## P11. 엑셀 리포트 [시스템 반영됨]

> CSV를 엑셀로 열 때 날짜가 ####로 보이는 문제를 없애기 위해 report.xlsx를
> 자동 생성. 날짜 형식·열 너비·틀 고정·필터 포함, 시트: 일별보유·종목손익·
> 거래기록·지표. 기존 폴더는 make_excel.py로 변환.
>
> 반영 위치: `src/excel_report.py`, `make_excel.py`, `requirements.txt`
> (openpyxl), `run_backtest.py`, `README.md`.

## P13. 스위프·풀 재구축 도구 [시스템 반영됨]

> 임계값 스위프용 `--set` 덮어쓰기와 `--workers` 조절, 야후 제한 대비
> 풀 수집 재시도 패스. 나스닥 상장 6239개로 풀 재구축 중(OTC 제외).
>
> 반영 위치: `run_backtest.py`(--set, --workers), `tools/build_pool.py`
> (--source, 패턴 필터, 재시도), `src/universe.py`(_parse_nasdaq).

## P12. 한국어 종목명 [시스템 반영됨]

> 티커만으로 종목을 알기 어려우니 discovery.csv·엑셀에 한국어명 열 추가.
> 전종목 한글 무료 소스가 없어 60종목 매핑 파일을 두고, 없는 티커는
> 티커 그대로 표시. 모르는 종목은 CSV에 한 줄 추가.
>
> 반영 위치: `data/stock_names_kr.csv`, `src/names.py`,
> `src/discovery.py`, `run_backtest.py`.
> 상태: 매핑 60개뿐이라 K안 거래 345종목은 티커 폴백. 풀 한글 소스 확보 전까지 유지.

## P9. v2 전략 실험 체계 [시스템 반영됨]

> 단기 신호 3종(rsi·macd·bb)을 `--signal`로 교체 실행. 지표풀(RSI·MACD·BB·MA)
> 을 엔진이 미리 계산해 컨텍스트로 전달하고, 헤드앤숄더 천장형 판정으로
> 상승곡선 보유종목의 리밸런싱 강제매도를 면제한다. 리밸런싱 2주, 현금 10% 고정.
>
> 반영 위치: `src/indicators.py`(macd·bb·ma), `src/patterns.py`,
> `src/backtest.py`(ctx), `src/strategies/my_strategy.py`(v2),
> `config.yaml`(2W, short 섹션), `run_backtest.py`(--signal).

---

## S1. 본 전략 기록 (본인 작성·수정 — 상태: v2.5)

> 근거 데이터는 모두 P0 기준(2023-12-31 이전)만 사용한다. 바꿀 때마다 변경
> 이력에 한 줄씩 추가한다.
>
> - 유니버스: 나스닥 상장 6239개 → 시세 수신 5753개 → 유동성 필터
>   (컷오프 이전 60일 평균 일대금 100만$ 이상) 3175개. 전략이 선정+리밸런싱.
>   EDGAR 10445개 방식은 OTC 잡음이 많아 폐기.
> - 펀더멘털: EDGAR companyfacts 확정치(filed≤컷오프 최신 10-K). 12월 결산사는
>   FY2022가 들어가는 것이 정상(P0 준수). 결측은 최하위 취급.
> - 바구니: 스윙 50% + 단기 40% + 현금 10% (리밸런싱 시 현금 10% 강제).
> - 스윙: PER+PBR 상위 9개 각 10% + 현금 10%. 리밸런싱 2주.
> - 단기 신호 3종 교체 실험: rsi(RSI 급락·반등) | macd(히스토그램 전환) |
>   bb(밴드 이탈·돌파). 임계값은 2023년 실험으로 튜닝.
> - 헤드앤숄더 규칙: 편입외 보유종목도 상승추세 + 천장형 없음이면 강제매도 면제.
> - 현금 10% + MMF 이자. 단기는 수일 보유 (일봉 종가 체결).
> - v3 후보: 진입가 기준 손절은 완료(ctx 평단 전달 + SHORT_STOP) — 잔여: 익절·보유일 청산.
>
> - 초기 시드 10억 (수익률 무관, 단위 규약).
> 변경 이력:
> - v1: 스윙50/단기40/현금10, 유니버스 파일화, 기간 2년 확정.
> - v2: 상위 9개+현금10% 고정, 2주 리밸런싱, 신호 3종 교체, H&S 면제 규칙.
> - v2.1: H&S 면제가 최하위 편입 대체(현금 유지), 리밸런싱 매도→매수 2패스.
> - v2.2: 신호 rsi 30/60 확정(2023 스위프 Sharpe 기준), 풀 재구축(nasdaq)+재시도.
> - v2.3: 회전율 튜닝 — 쿨다운5일 확정(2023년 15.5%/Sharpe 1.20, 밴드 확장은 탈락).
>   저회전 (20/70)은 9.4%/0.72로 유지, 본선 후보에서 제외.
> - 개발 절차: 2023년 실험(experiment, 설계 ≤2022-12-31, outputs_exp) →
>   통과 시 2024~2025 본 백테스트(final). 2023 결과로 2024 설정을 바꾸면 뒷북.
> - v2.4: 풀 스윕 확정 — 저회전 C안(rsi_buy=20, rsi_sell=70, cooldown 10일, band 0.02)이
>   양 기간 모두 B&H 초과한 유일안. 2023년 7안(2824종목): A(30/70) 60.8%/Sharpe 1.90 >
>   F(bb) 35.4%/1.39 > C 30.9%/1.15 > D(75) 24.0% > E(macd) 21.3% > 기준(30/60) 13.8%/0.67.
>   본선(2024~2025, 3175종목, B&H 27.2%): C CAGR 19.9%/0.76/초과 +16.4pp >
>   A 2.2%/0.21/초과 -22.8pp > F -2.2%/-0.00. A안은 2023 과적합 판정(늦은 매도가
>   상승장에서만 유효). 풀 본선 명령: --universe pool --mode final + --set 4종.
> - 거래이력 한눈보기(trade_history_view.csv): 순번·날짜·구분·종목·종목명·수량·체결가·
>   거래금액·수수료·사유·실현손익·실현수익률%·종목누적손익·보유일수·거래후현금·총자산·
>   누적수익률%. 한글헤더+BOM이라 엑셀에서 바로 열림. run_backtest가 매 실행마다 자동 생성.
> - 지표 내부 파라미터 배선: MACD(12/26/9)·BB(20/2.0)가 엔진 하드코딩이었음을 확인.
>   build_indicators 분리 + short 섹션(macd_fast/slow/signal, bb_window/bb_std, 기존 rsi_window)으로
>   조정 가능. 2023 풀 4안: J(BB 10/1.9) 28.2%/1.24 > G(RSI7) 24.0% > H(RSI21) 22.1% >
>   I(MACD 5/35/5) 1.5%. J를 본선 검증했더니 -2.5%(초과 -32pp, 11742건)로 붕괴 — 과적합.
>   C안(RSI14 20/70)이 최종 베스트 유지.
> - 손절 추가(구조적 구멍): 손절이 없어 SMX 단일 -86.6%, GMM -7.4천만(-51.6%) 등
>   -30% 이하 14건 방치. ctx에 평단(cost) 전달 + tactical 평단 대비 stop_loss 전량매도
>   (SHORT_STOP, trade_view 손절매 표기). 2023 풀: K(10%) 40.8%/1.41 > C 30.9% >
>   L(20%) 10.0%. 본선: K CAGR 42.6%/Sharpe 1.39/초과 +75.4pp/MDD -17.8%로 양 기간
>   모두 C를 이겨 새 베스트. 바닥이 -4.6천만으로 잘림. 단 EBS 편중(+2.3억)과
>   회전율 75배(수수료 9.4천만)는 남음. M(15%)은 2023년 13.7%/0.66으로 탈락
>   (10→15→20%: 40.8→13.7→10.0, 레벨 민감도 큼 — A안 과적합과 동급 주의).
> - v2.5: config.yaml을 K안으로 승격(rsi 20/70, 쿨다운10, 밴드0.02, 손절10%).
>   --set 없이 본선 재현 확인(동일 1800건·CAGR 42.6%). 60종목 v2.3 수치는 위 이력 참조.
> - 정리: K안 산출물은 result/로 개명(제출용). 나머지 outputs_* 34개는
>   outputs_archive/로 이동. 본 파일의 outputs_exp/풀 스위프 경로는 아카이브 안에서 참조.
> - 리팩토링: 프로젝트 전체를 AI퀀트/로 이동(코드 경로 상대참조라 무수정, 38테스트 통과).
>   실행은 AI퀀트/에서 (`.venv\Scripts\python.exe run_backtest.py ...`).
> - P기록: 풀 NASDAQ 6239→수신 5753→유동성 3175(2022-10-01~2025-12-31, 813일).
>   상장폐지 꼬리 NaN은 ffill 최종가 평탄화(선행 NaN 유지, 미래정보 미사용) — 미처리 시
>   2024-10-16부터 equity NaN으로 본선이 중단됨. EDGAR FY는 filed≤컷오프 10-K만
>   (본선 1450/3175 확보, 결측 최하위). 콘솔 cp949 크래시 수정(— → -).

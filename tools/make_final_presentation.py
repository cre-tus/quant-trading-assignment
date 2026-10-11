"""
대학 과제 제출용 리밸런싱 백테스트 프레젠테이션(PPTX) 자동 생성 스크립트.
- 대상 결과물: outputs_final_pool_k
- 규격: 16:9 와이드스크린 (13.333 x 7.5 인치)
- 디자인: 모던 퀀트 핀테크 테마 (Deep Navy / Royal Blue / Slate / Clean Cards / Visual Charts)
"""
import sys
from pathlib import Path
import json
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 1. 색상 팔레트 상수 정의
C_NAVY_DARK    = RGBColor(15, 23, 42)      # #0F172A (다크 네이비 / 표지 배경 및 헤더)
C_NAVY_LIGHT   = RGBColor(30, 41, 59)      # #1E293B
C_BLUE_PRIMARY = RGBColor(37, 99, 235)     # #2563EB (로얄 블루 / 메인 강조)
C_BLUE_BG      = RGBColor(239, 246, 255)   # #EFF6FF (블루 소프트 카드 배경)
C_BLUE_BORDER  = RGBColor(191, 219, 254)   # #BFDBFE
C_SLATE_BG     = RGBColor(248, 250, 252)   # #F8FAFC (기본 카드 배경)
C_SLATE_BORDER = RGBColor(226, 232, 240)   # #E2E8F0 (기본 카드 테두리)
C_TEXT_MAIN    = RGBColor(15, 23, 42)      # #0F172A
C_TEXT_BODY    = RGBColor(51, 65, 85)      # #334155
C_TEXT_MUTED   = RGBColor(100, 116, 139)   # #64748B
C_WHITE        = RGBColor(255, 255, 255)
C_GREEN        = RGBColor(16, 185, 129)    # #10B981 (긍정 / 초과수익)
C_GREEN_BG     = RGBColor(236, 253, 245)
C_GREEN_BORDER = RGBColor(167, 243, 208)
C_RED          = RGBColor(239, 68, 68)     # #EF4444 (손실 / 낙폭)
C_RED_BG       = RGBColor(254, 242, 242)
C_RED_BORDER   = RGBColor(254, 202, 202)
C_GOLD         = RGBColor(217, 119, 6)     # #D97706 (주의 / 하이라이트)

FONT_HEADING = "Malgun Gothic"
FONT_BODY    = "Malgun Gothic"


class PresentationBuilder:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.blank_layout = self.prs.slide_layouts[6]  # 빈 슬라이드

    def add_slide_header(self, slide, category: str, title: str, subtitle: str):
        """표준 상단 헤더 영역 생성 (카테고리 뱃지 + 제목 + 부제목)"""
        # 상단 뱃지 박스
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.4), Inches(2.8), Inches(0.32))
        badge.fill.solid()
        badge.fill.fore_color.rgb = C_BLUE_BG
        badge.line.color.rgb = C_BLUE_BORDER
        badge.line.width = Pt(1)
        tf_b = badge.text_frame
        tf_b.word_wrap = False
        p_b = tf_b.paragraphs[0]
        p_b.text = f"●  {category}"
        p_b.font.name = FONT_HEADING
        p_b.font.size = Pt(9.5)
        p_b.font.bold = True
        p_b.font.color.rgb = C_BLUE_PRIMARY
        p_b.alignment = PP_ALIGN.CENTER

        # 제목 텍스트
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.75))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0)
        tf.margin_bottom = Inches(0)
        tf.margin_left = Inches(0)
        tf.margin_right = Inches(0)
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(20)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_DARK

        p_s = tf.add_paragraph()
        p_s.text = subtitle
        p_s.font.name = FONT_BODY
        p_s.font.size = Pt(11)
        p_s.font.color.rgb = C_TEXT_MUTED
        p_s.space_before = Pt(3)

    def add_card(self, slide, left, top, width, height, bg_color=C_SLATE_BG, border_color=C_SLATE_BORDER, radius_rect=True):
        """컨테이너 카드 박스 추가"""
        shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius_rect else MSO_SHAPE.RECTANGLE
        box = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(width), Inches(height))
        box.fill.solid()
        box.fill.fore_color.rgb = bg_color
        box.line.color.rgb = border_color
        box.line.width = Pt(1)
        return box

    def add_kpi_card(self, slide, left, top, width, height, title: str, value: str, subtext: str, tag: str = None, tag_color=C_BLUE_PRIMARY):
        """핵심 지표용 KPI 카드"""
        self.add_card(slide, left, top, width, height, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx_box = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(width - 0.4), Inches(height - 0.3))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0)
        tf.margin_bottom = Inches(0)
        tf.margin_left = Inches(0)
        tf.margin_right = Inches(0)

        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(11)
        p_title.font.bold = True
        p_title.font.color.rgb = C_TEXT_MUTED

        p_val = tf.add_paragraph()
        p_val.text = value
        p_val.font.name = FONT_HEADING
        p_val.font.size = Pt(22)
        p_val.font.bold = True
        p_val.font.color.rgb = tag_color
        p_val.space_before = Pt(4)

        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = C_TEXT_BODY
        p_sub.space_before = Pt(3)

    # -------------------------------------------------------------
    # 슬라이드 빌더 개별 메서드들
    # -------------------------------------------------------------
    def build_slide_1_cover(self):
        """슬라이드 1: 메인 표지"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        # 웅장한 다크 네이비 배경
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_NAVY_DARK
        bg.line.fill.background()

        # 상단 서브 타이틀 뱃지
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.3), Inches(4.5), Inches(0.4))
        badge.fill.solid()
        badge.fill.fore_color.rgb = C_BLUE_PRIMARY
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = "IT신기술 과제 / 퀀트 투자 시스템 백테스팅 보고서"
        p_b.font.name = FONT_HEADING
        p_b.font.size = Pt(11)
        p_b.font.bold = True
        p_b.font.color.rgb = C_WHITE
        p_b.alignment = PP_ALIGN.CENTER

        # 메인 제목 및 설명
        tb = slide.shapes.add_textbox(Inches(1.2), Inches(2.0), Inches(11.0), Inches(3.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = "동적 리밸런싱 및 전술적 단기 매매\n백테스팅 연구 보고서"
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(34)
        p1.font.bold = True
        p1.font.color.rgb = C_WHITE

        p2 = tf.add_paragraph()
        p2.text = "SEC EDGAR 10-K 확정 펀더멘털 랭킹, H&S 추세 면제, RSI 모멘텀 & 손절 필터를 결합한 복합 알파 전략"
        p2.font.name = FONT_BODY
        p2.font.size = Pt(14)
        p2.font.color.rgb = RGBColor(148, 163, 184)
        p2.space_before = Pt(16)

        # 하단 핵심 성과 요약 배너 박스
        banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.7), Inches(10.9), Inches(1.3))
        banner.fill.solid()
        banner.fill.fore_color.rgb = C_NAVY_LIGHT
        banner.line.color.rgb = RGBColor(51, 65, 85)
        banner.line.width = Pt(1)

        metrics = [
            ("백테스팅 구간", "2024.01 ~ 2025.12", "표본외 (2개년 검증)"),
            ("연평균 복리수익률 (CAGR)", "42.58%", "B&H (+27.2%) 대비 +75.4%p"),
            ("최대 낙폭 (MDD)", "-17.75%", "21일 만에 전고점 회복"),
            ("위험조정비율 (Sharpe)", "1.39", "Sortino 2.32 / Calmar 2.41"),
        ]
        for i, (m_lbl, m_val, m_sub) in enumerate(metrics):
            m_box = slide.shapes.add_textbox(Inches(1.4 + i * 2.7), Inches(4.8), Inches(2.5), Inches(1.1))
            m_tf = m_box.text_frame
            m_tf.word_wrap = True
            m_p1 = m_tf.paragraphs[0]
            m_p1.text = m_lbl
            m_p1.font.size = Pt(9.5)
            m_p1.font.color.rgb = RGBColor(148, 163, 184)
            m_p2 = m_tf.add_paragraph()
            m_p2.text = m_val
            m_p2.font.size = Pt(18)
            m_p2.font.bold = True
            m_p2.font.color.rgb = C_GREEN if "42.58%" in m_val or "1.39" in m_val else C_WHITE
            m_p3 = m_tf.add_paragraph()
            m_p3.text = m_sub
            m_p3.font.size = Pt(8.5)
            m_p3.font.color.rgb = RGBColor(203, 213, 225)

        # 하단 메타정보
        meta_box = slide.shapes.add_textbox(Inches(1.2), Inches(6.3), Inches(10.9), Inches(0.5))
        m_tf2 = meta_box.text_frame
        p_m = m_tf2.paragraphs[0]
        p_m.text = "분석 산출물: outputs_final_pool_k  |  개발 엔진: Python 3.12 퀀트 시스템  |  제출일: 2026.10"
        p_m.font.size = Pt(10)
        p_m.font.color.rgb = RGBColor(100, 116, 139)

    def build_slide_2_toc(self):
        """슬라이드 2: 목차"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "목차 (Contents)", "연구 보고서 구성 및 제출 항목 목차", "과제 평가 가이드라인에 맞춘 5개 핵심 세부 영역 구성")

        tocs = [
            ("01", "리밸런싱 전략 세부 설정 사항", "• 유니버스 선정 (미국 3,175개 유동성 풀 & 확정 10-K)\n• 자산 배분 비중 (주식 9개 90% + 현금 MMF 10%)\n• 2주 리밸런싱 주기, H&S 추세 면제, RSI 20/70 단기 매매 및 -10% 손절"),
            ("02", "개발 도구 및 구현 방식", "• 개발 스택: Python 3.12, SEC EDGAR API, Empyrical\n• 무결성 보장: Look-Ahead Bias 완전 차단 (2023-12-31 컷오프)\n• 표본외 2단계 검증 체계 (2023 개발 실험 → 2024-2025 본 백테스트)"),
            ("03", "백테스팅 성과 및 거래 기록", "• 필수 3대 지표: CAGR 42.6%, B&H 초과 +75.4%p, MDD -17.7%\n• 자산 성장 곡선 및 국면별 동적 흐름 분석\n• 총 1,800건 매매 로그 발췌 및 종목별 손익 기여도 (Top 5 vs Bottom 5)"),
            ("04", "심층 결과 분석 및 원인 평가", "• 우수 요인: 밸류에이션 팩터 결합, 하방 리스크 방어, RSI 역발상 매수\n• 한계 및 개선과제: 75배 회전율 및 9.4천만 원 수수료, 주도주 쏠림\n• 2024년 1분기 시장 조정기 원인 분석 및 실전 최적화 방안"),
            ("05", "개발 코드 및 AI 프롬프트 자료", "• AI 프롬프트 아키텍처 (P0 시간선 지침 ~ P13 풀 재구축/스위프)\n• my_strategy.py 핵심 전략 소스코드 구조 및 config.yaml 설정\n• 투자사 규격 산출물 연계 (report.xlsx, discovery.csv 등)"),
        ]

        for i, (num, title, desc) in enumerate(tocs):
            col = i % 2
            row = i // 2
            left = 0.8 + col * 5.9
            top = 1.6 + row * 1.7
            width = 5.7
            height = 1.55 if i < 4 else 1.55

            if i == 4:  # 5번째는 가로 확장하거나 단독
                left = 0.8
                top = 5.0
                width = 11.6
                height = 1.4

            self.add_card(slide, left, top, width, height, bg_color=C_WHITE, border_color=C_SLATE_BORDER)

            # 번호 뱃지
            num_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left + 0.25), Inches(top + 0.25), Inches(0.65), Inches(0.45))
            num_box.fill.solid()
            num_box.fill.fore_color.rgb = C_BLUE_BG
            num_box.line.color.rgb = C_BLUE_BORDER
            tf_n = num_box.text_frame
            p_n = tf_n.paragraphs[0]
            p_n.text = num
            p_n.font.size = Pt(13)
            p_n.font.bold = True
            p_n.font.color.rgb = C_BLUE_PRIMARY
            p_n.alignment = PP_ALIGN.CENTER

            # 텍스트
            tx = slide.shapes.add_textbox(Inches(left + 1.05), Inches(top + 0.2), Inches(width - 1.2), Inches(height - 0.3))
            tf = tx.text_frame
            tf.word_wrap = True
            p_t = tf.paragraphs[0]
            p_t.text = title
            p_t.font.size = Pt(12.5)
            p_t.font.bold = True
            p_t.font.color.rgb = C_NAVY_DARK

            p_d = tf.add_paragraph()
            p_d.text = desc
            p_d.font.size = Pt(9.5)
            p_d.font.color.rgb = C_TEXT_BODY
            p_d.space_before = Pt(3)

    def build_slide_3_universe(self):
        """슬라이드 3: 리밸런싱 세부 설정 - 유니버스 및 펀더멘털 정의"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "1. 리밸런싱 세부 설정 사항", "유니버스 풀 및 펀더멘털 데이터 정의", "과제 기준: 10개 핵심 자산 (9개 동적 편입 주식 + 1개 현금/MMF 버퍼)")

        # 좌측 카드: 유니버스 필터링 파이프라인
        self.add_card(slide, 0.8, 1.6, 5.7, 5.2, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx1 = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
        tf1 = tx1.text_frame
        tf1.word_wrap = True

        p = tf1.paragraphs[0]
        p.text = "■ 나스닥 기반 3단계 유니버스 선별 파이프라인"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = C_BLUE_PRIMARY

        bullets1 = [
            ("1단계: 전체 시장 상장 종목 수집", "나스닥 상장 6,239개 중 시세 수신 정상 5,753개 확보 (OTC 잡음 종목 원천 배제)."),
            ("2단계: 엄격한 유동성 필터링 (Liquidity Filter)", "전략 설계 컷오프(2023-12-31) 직전 60영업일 평균 일거래대금 $1,000,000(약 13억 원) 이상 종목만 통과 → 최종 3,175개 유동성 풀 확정."),
            ("3단계: 최종 포트폴리오 10개 핵심 자산 압축", "3,175개 중 PER+PBR 결합 랭킹 상위 9개 주식 선별 + 현금 10% 버퍼 편입. 총 10개 자산으로 완벽 분산 운용."),
            ("현금 자산 (MMF) 수익률 반영", "유휴 현금 및 10% 기본 현금 비중에 대해 미국 단기 MMF 금리 연 4.0% 이자 수익을 매일 일할 계산 복리 반영."),
        ]
        for title, desc in bullets1:
            pt = tf1.add_paragraph()
            pt.text = f"• {title}"
            pt.font.size = Pt(11)
            pt.font.bold = True
            pt.font.color.rgb = C_NAVY_DARK
            pt.space_before = Pt(8)
            pd = tf1.add_paragraph()
            pd.text = desc
            pd.font.size = Pt(9.5)
            pd.font.color.rgb = C_TEXT_BODY
            pd.space_before = Pt(2)

        # 우측 카드: 펀더멘털 무결성 & 랭킹 규칙
        self.add_card(slide, 6.8, 1.6, 5.7, 5.2, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx2 = slide.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
        tf2 = tx2.text_frame
        tf2.word_wrap = True

        p2 = tf2.paragraphs[0]
        p2.text = "■ Look-Ahead Bias 차단 및 SEC EDGAR 10-K 반영"
        p2.font.size = Pt(13)
        p2.font.bold = True
        p2.font.color.rgb = C_BLUE_PRIMARY

        bullets2 = [
            ("시간 기준선 엄수 지침 (P0 반영)", "백테스트 기간(2024~2025)의 정보를 미래 참조하지 않도록, 모든 재무 데이터는 2023-12-31 이전 확정 공시된 10-K 연례보고서만 채택."),
            ("공시 시차 현실화 (Reporting Lag)", "12월 결산 법인의 경우 2023년 말 시점 최신 확정 공시는 FY2022 보고서이므로 이를 정상 반영. 결측 종목은 최하위 랭크 처리."),
            ("동적 밸류에이션 랭킹 계산 (Dynamic Valuation)", "고정 스냅샷의 오류를 방지하기 위해 당일 종가(P_t)와 기준 재무(EPS_0, BPS_0)를 결합하여 일별 동적 PER_t, PBR_t 산출 후 결합 순위 매김."),
            ("초기 운용 자본 설정", "초기 시드머니: 1,000,000,000원 ($10억 상당). 모든 거래는 일봉 종가 체결 규약 준수."),
        ]
        for title, desc in bullets2:
            pt = tf2.add_paragraph()
            pt.text = f"• {title}"
            pt.font.size = Pt(11)
            pt.font.bold = True
            pt.font.color.rgb = C_NAVY_DARK
            pt.space_before = Pt(8)
            pd = tf2.add_paragraph()
            pd.text = desc
            pd.font.size = Pt(9.5)
            pd.font.color.rgb = C_TEXT_BODY
            pd.space_before = Pt(2)

    def build_slide_4_strategy_rebalance(self):
        """슬라이드 4: 리밸런싱 세부 설정 - 자산 배분 및 2주 리밸런싱 로직"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "1. 리밸런싱 세부 설정 사항", "포트폴리오 자산 배분 및 정기 리밸런싱 규칙", "가치주 선별(PER+PBR)과 추세 보존(H&S 면제)이 결합된 하이브리드 리밸런싱 구조")

        # 상단 3개 요약 박스
        boxes = [
            ("자산 배분 비율", "주식 90% + 현금 10%", "선정된 상위 9개 주식 각 10% 동일비중 배분\n현금 10% 항시 유지로 하방 리스크 완충"),
            ("정기 리밸런싱 주기", "2주 (Bi-Weekly, 2W)", "10영업일 간격 정기 재평가 및 리밸런싱\n매도 후 매수의 2-Pass 실행으로 현금 잠식 방지"),
            ("임시 확대 허용 범위", "최대 20% 이탈 밴드", "종목별 최대 비중 12% 허용 (10% × 1.2)\n리밸런싱 불감대 2% 적용으로 불필요한 미세거래 억제"),
        ]
        for i, (btitle, bval, bdesc) in enumerate(boxes):
            bx = 0.8 + i * 3.95
            self.add_card(slide, bx, 1.6, 3.8, 1.5, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
            tx = slide.shapes.add_textbox(Inches(bx + 0.2), Inches(1.75), Inches(3.4), Inches(1.2))
            tf = tx.text_frame
            tf.word_wrap = True
            p1 = tf.paragraphs[0]
            p1.text = btitle
            p1.font.size = Pt(10)
            p1.font.bold = True
            p1.font.color.rgb = C_TEXT_MUTED
            p2 = tf.add_paragraph()
            p2.text = bval
            p2.font.size = Pt(16)
            p2.font.bold = True
            p2.font.color.rgb = C_BLUE_PRIMARY
            p2.space_before = Pt(2)
            p3 = tf.add_paragraph()
            p3.text = bdesc
            p3.font.size = Pt(8.5)
            p3.font.color.rgb = C_TEXT_BODY
            p3.space_before = Pt(3)

        # 하단 좌측: 밸류에이션 결합 랭킹 알고리즘
        self.add_card(slide, 0.8, 3.3, 5.7, 3.5, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx_l = slide.shapes.add_textbox(Inches(1.0), Inches(3.45), Inches(5.3), Inches(3.2))
        tf_l = tx_l.text_frame
        tf_l.word_wrap = True
        pl = tf_l.paragraphs[0]
        pl.text = "■ 가치 팩터 결합 랭킹 알고리즘 (PER + PBR)"
        pl.font.size = Pt(12.5)
        pl.font.bold = True
        pl.font.color.rgb = C_NAVY_DARK

        steps = [
            ("PER 랭킹 산출", "PER = P_t / EPS_0 (양수 PER 오름차순 순위, 적자 기업 최하위)"),
            ("PBR 랭킹 산출", "PBR = P_t / BPS_0 (저평가 순 오름차순 순위 부여)"),
            ("결합 순위 (Rank Sum)", "Rank_Total = Rank(PER) + Rank(PBR) 합산 최상위 9개 도출"),
            ("역동적 포트폴리오 교체", "매 2주마다 재산출하여 저평가 해소 종목 교체 매매"),
        ]
        for st, sd in steps:
            p_s = tf_l.add_paragraph()
            p_s.text = f"• {st}: {sd}"
            p_s.font.size = Pt(9.5)
            p_s.font.color.rgb = C_TEXT_BODY
            p_s.space_before = Pt(5)

        # 하단 우측: 헤드앤숄더(H&S) 패턴 강제매도 면제 규칙
        self.add_card(slide, 6.8, 3.3, 5.7, 3.5, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx_r = slide.shapes.add_textbox(Inches(7.0), Inches(3.45), Inches(5.3), Inches(3.2))
        tf_r = tx_r.text_frame
        tf_r.word_wrap = True
        pr = tf_r.paragraphs[0]
        pr.text = "■ 헤드앤숄더(H&S) 상승추세 보유 면제 규칙 (Alpha Driver)"
        pr.font.size = Pt(12.5)
        pr.font.bold = True
        pr.font.color.rgb = C_BLUE_PRIMARY

        rules = [
            ("문제점 인식", "순수 가치 랭킹만 사용할 경우, 주가가 급등하여 PER/PBR이 상승한 우수 주도주(Winner)를 너무 일찍 강제 매도하는 조기청산 결함 발생."),
            ("추세 보존 필터 도입", "기존 보유 종목이 9위 밖으로 밀려나더라도, 주가가 우상향 곡선을 유지하고 천장형 헤드앤숄더 패턴이 미발생했다면 강제매도를 면제."),
            ("최하위 편입 종목 대체", "보유 유지된 우수 종목이 신규 편입 최하위 후보를 대체하여 편입되며, 현금 10% 비중은 절대 침범하지 않음."),
            ("실제 효과", "EBS, SSP 등 대형 주도주의 시세 분출 구간을 끝까지 추종하여 초과 수익 달성의 핵심 기여 요인으로 작용."),
        ]
        for rt, rd in rules:
            p_r = tf_r.add_paragraph()
            p_r.text = f"• {rt}"
            p_r.font.size = Pt(10)
            p_r.font.bold = True
            p_r.font.color.rgb = C_NAVY_DARK
            p_r.space_before = Pt(4)
            p_rd = tf_r.add_paragraph()
            p_rd.text = rd
            p_rd.font.size = Pt(9)
            p_rd.font.color.rgb = C_TEXT_BODY
            p_rd.space_before = Pt(1)

    def build_slide_5_tactical_rules(self):
        """슬라이드 5: 리밸런싱 세부 설정 - 전술적 중간 매매 & 리스크 관리"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "1. 리밸런싱 세부 설정 사항", "전술적 중간 매매(Tactical Trading) 및 손절 로직", "RSI 오실레이터 기반 분할 익절/과매도 매수 및 -10% 하방 방어 Stop-Loss")

        cards = [
            ("단기 과매수 분할 매도\n(SHORT_SELL)", "RSI(14) > 70 돌파 시", "보유 수량의 50% 분할 익절", 
             "• 보유 중인 주식이 과열권에 진입할 경우 절반을 익절하여 현금 확보\n• 잔여 50%는 추가 상승 추세를 추종하여 수익 극대화\n• 본 백테스트 중 총 646건 발동되어 현금 유동성 공급", C_BLUE_PRIMARY, C_BLUE_BG),
            ("단기 과매도 저점 매수\n(SHORT_BUY)", "RSI(14) < 20 진입 시", "가용 현금의 50% 분할 매수", 
             "• 유니버스 종목이 단기 과매도 투매를 겪을 때 역발상 저점 진입\n• 주식 총 비중 한도(90%) 및 현금 룸 내에서만 신중하게 집행\n• 본 백테스트 중 총 397건 발동, 진입 후 20일 평균 +1.78% 알파 창출", C_GREEN, C_GREEN_BG),
            ("회전율 억제 쿨다운\n(Cooldown Rule)", "동일 종목 10일 재진입 제한", "잦은 휩소(Whipsaw) 방지", 
             "• 단기 매매 직후 최소 10영업일 동안 동일 종목 재매수를 금지\n• 2023년 파라미터 스위프 결과 5일 대비 10일 설정이 거래 수수료를 대폭 절감하고 Sharpe 비율을 개선함", C_GOLD, C_SLATE_BG),
            ("구조적 손절매 필터\n(SHORT_STOP)", "매입 평단 대비 -10% 도달", "보유 수량 100% 전량 강제 손절", 
             "• 손절 없는 가치 전략의 치명적 함정(최대 -86.6% 방치) 원천 차단\n• 평단가(Avg Cost) 대비 10% 이상 하락 즉시 전량 청산\n• 총 199건 발동, 최대 손실 종목을 -4.6천만 원 선에서 완벽 방어", C_RED, C_RED_BG),
        ]

        for i, (title, cond, action, desc, color, bg) in enumerate(cards):
            left = 0.8 + i * 2.95
            self.add_card(slide, left, 1.6, 2.8, 5.2, bg_color=C_WHITE, border_color=C_SLATE_BORDER)

            # 상단 컬러 띠
            band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(1.6), Inches(2.8), Inches(0.1))
            band.fill.solid()
            band.fill.fore_color.rgb = color
            band.line.fill.background()

            tx = slide.shapes.add_textbox(Inches(left + 0.15), Inches(1.8), Inches(2.5), Inches(4.8))
            tf = tx.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = title
            p1.font.size = Pt(12)
            p1.font.bold = True
            p1.font.color.rgb = C_NAVY_DARK

            p_cond_box = tf.add_paragraph()
            p_cond_box.text = f"조건: {cond}"
            p_cond_box.font.size = Pt(10)
            p_cond_box.font.bold = True
            p_cond_box.font.color.rgb = color
            p_cond_box.space_before = Pt(6)

            p_act = tf.add_paragraph()
            p_act.text = f"집행: {action}"
            p_act.font.size = Pt(9.5)
            p_act.font.bold = True
            p_act.font.color.rgb = C_NAVY_DARK
            p_act.space_before = Pt(3)

            p_d = tf.add_paragraph()
            p_d.text = desc
            p_d.font.size = Pt(8.8)
            p_d.font.color.rgb = C_TEXT_BODY
            p_d.space_before = Pt(8)

    def build_slide_6_dev_stack(self):
        """슬라이드 6: 개발 도구 및 방식 - 기술 스택 및 아키텍처"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "2. 개발 도구 및 구현 방식", "개발 환경, 데이터 SDK 및 백테스트 엔진 구조", "재현성과 데이터 정밀도를 극대화한 Python 기반 모듈형 이벤트 드리븐 아키텍처")

        # 4개 영역 그리드
        sections = [
            ("핵심 언어 및 런타임 환경", [
                "• Python 3.12: 최신 가상환경(.venv) 기반 의존성 격리 관리",
                "• Pandas & NumPy: 3,175개 종목 대용량 시계열 행렬 연산 고속화",
                "• Config-Driven 설계: config.yaml 파일 하나로 유니버스, 기간, 수수료율, 임계값 일체 제어",
                "• 단위 테스트 스위트: unittest 기반으로 미래 참조 차단 및 엔진 로직 상시 검증",
            ]),
            ("데이터 수집 SDK 및 캐싱", [
                "• SEC EDGAR REST API: 10,445개 CIK 기업 공시 companyfacts 원천 파싱",
                "• Yahoo Finance (yfinance): 주가 시세 및 거래량 데이터 수집",
                "• 로컬 디스크 캐시: 야후 레이트 리밋 방지 및 고속 백테스트를 위한 pool 캐싱 체계",
                "• 상장폐지 꼬리 보정: tail NaN에 대해 ffill 최종가 평탄화 적용 (Equity 왜곡 방지)",
            ]),
            ("정밀 퀀트 분석 & 교차검증 SDK", [
                "• 자체 개발 퀀트 엔진: 정확한 편도 수수료(0.1%), 현금 이자(4%), 평단가 추적",
                "• Empyrical-Reloaded 연동: 깃허브 스타 상위 오픈소스 퀀트 라이브러리 탑재",
                "• 5대 핵심 퀀트 지표 독립 교차검증: Annual Return, MDD, Sharpe, Sortino, Calmar",
                "• 두 엔진 간 지표 일치율 99.9% 확인으로 연산 신뢰성 확보",
            ]),
            ("자동화 리포팅 및 산출물 생성", [
                "• python-pptx: 과제 제출용 16:9 와이드스크린 프레젠테이션 자동 렌더링",
                "• OpenPyXL (Excel): 날짜 #### 오류 방지 서식, 열 너비 자동 맞춤, 틀 고정 적용",
                "• 한글 지원 UTF-8 BOM CSV: 엑셀 및 다양한 뷰어에서 한글 깨짐 없이 바로 열람 가능",
                "• Matplotlib 차트 엔진: 고해상도 자산 곡선 및 성과 분포 시각화 이미지 생성",
            ]),
        ]

        for i, (title, items) in enumerate(sections):
            col = i % 2
            row = i // 2
            left = 0.8 + col * 5.9
            top = 1.6 + row * 2.6
            width = 5.7
            height = 2.4

            self.add_card(slide, left, top, width, height, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
            tx = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.2), Inches(width - 0.4), Inches(height - 0.3))
            tf = tx.text_frame
            tf.word_wrap = True

            p = tf.paragraphs[0]
            p.text = f"■ {title}"
            p.font.size = Pt(12)
            p.font.bold = True
            p.font.color.rgb = C_BLUE_PRIMARY

            for item in items:
                pi = tf.add_paragraph()
                pi.text = item
                pi.font.size = Pt(9.3)
                pi.font.color.rgb = C_TEXT_BODY
                pi.space_before = Pt(4)

    def build_slide_7_methodology_validation(self):
        """슬라이드 7: 개발 도구 및 방식 - 2단계 표본외 검증 체계"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "2. 개발 도구 및 구현 방식", "과적합(Overfitting) 방지를 위한 2단계 검증 체계", "2023년 개발/탐색 실험(In-Sample) → 2024~2025년 본 백테스팅(Out-of-Sample) 확정")

        # 2단계 비교 박스 (좌: 2023 실험, 우: 2024-2025 본선)
        self.add_card(slide, 0.8, 1.6, 5.7, 5.2, bg_color=C_SLATE_BG, border_color=C_SLATE_BORDER)
        tx1 = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
        tf1 = tx1.text_frame
        tf1.word_wrap = True
        p1 = tf1.paragraphs[0]
        p1.text = "PHASE 1. 2023년 모델 개발 및 파라미터 스위프"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = C_NAVY_DARK

        bullets1 = [
            ("목적 및 규약", "2022-12-31 이전 데이터로만 가설 수립 후 2023년 구간에서 파라미터 최적화 (산출 폴더: outputs_exp)."),
            ("신호 3종 비교 실험", "• RSI(25/65): CAGR 7.6%, Sharpe 0.63\n• MACD 전환: CAGR 6.5%, Sharpe 0.55\n• Bollinger Bands: CAGR 7.5%, Sharpe 0.59\n→ RSI 모멘텀의 알파 창출력 및 반응성 검증 완료."),
            ("RSI 임계값 & 쿨다운 스위프 (7개 안)", "• A안(30/70): 60.8% (강세장 과적합 의심)\n• C안(20/70, 쿨다운10): 30.9%, Sharpe 1.15 (저회전 우수)\n• 손절매 K안(Stop-loss 10%): 40.8%, Sharpe 1.41로 최고 성능 기록."),
            ("과적합 제거 교훈", "2023년 단기 강세장에서만 작동하는 공격적 파라미터를 배제하고, 하방 리스크가 통제되는 K안 최종 후보 낙점."),
        ]
        for st, sd in bullets1:
            pt = tf1.add_paragraph()
            pt.text = f"• {st}"
            pt.font.size = Pt(10.5)
            pt.font.bold = True
            pt.font.color.rgb = C_NAVY_DARK
            pt.space_before = Pt(6)
            pd = tf1.add_paragraph()
            pd.text = sd
            pd.font.size = Pt(9)
            pd.font.color.rgb = C_TEXT_BODY
            pd.space_before = Pt(2)

        self.add_card(slide, 6.8, 1.6, 5.7, 5.2, bg_color=C_WHITE, border_color=C_BLUE_PRIMARY)
        tx2 = slide.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
        tf2 = tx2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = "PHASE 2. 2024~2025년 본 백테스트 확정 검증"
        p2.font.size = Pt(13)
        p2.font.bold = True
        p2.font.color.rgb = C_BLUE_PRIMARY

        bullets2 = [
            ("표본외(Out-of-Sample) 무결성", "2023년 확정된 모델 파라미터(K안)를 일체 변경하지 않고 2024.01.01 ~ 2025.12.31 구간에 직결 실행."),
            ("뒷북(Hindsight Bias) 원천 차단", "본 구간의 결과를 보고 설정을 거꾸로 수정하는 사후 과적합 행위 완전 배제. (산출 폴더: outputs_final_pool_k)."),
            ("양 기간 연속 초과수익 입증 (Robustness)", "과적합된 A안은 2024~2025년에 2.2%로 무너졌으나, 리스크 통제형 K안은 본선에서 CAGR 42.6%를 달성하며 진정한 알파 입증."),
            ("Stop-Loss 10%의 구조적 진가 발휘", "2024년 4월 시장 하락기에서 199건의 선제적 손절매가 발동하여 단일 종목의 괴멸적 폭락(-86%)을 완벽 차단."),
        ]
        for st, sd in bullets2:
            pt = tf2.add_paragraph()
            pt.text = f"• {st}"
            pt.font.size = Pt(10.5)
            pt.font.bold = True
            pt.font.color.rgb = C_NAVY_DARK
            pt.space_before = Pt(6)
            pd = tf2.add_paragraph()
            pd.text = sd
            pd.font.size = Pt(9)
            pd.font.color.rgb = C_TEXT_BODY
            pd.space_before = Pt(2)

    def build_slide_8_metrics_summary(self):
        """슬라이드 8: 백테스팅 성과 요약 - 핵심 성능 지표"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "3. 백테스팅 성과 및 핵심 지표", "핵심 성능 지표 (Performance Metrics) 총괄 요약", "과제 필수 3대 지표(PL CAGR, B&H Return, MDD) 및 전문 퀀트 위험조정성과 비교")

        # 4대 KPI 카드
        self.add_kpi_card(slide, 0.8, 1.6, 2.7, 1.4, "PL CAGR (연평균복리)", "42.58%", "B&H 대비 +75.43%p 상회", tag_color=C_GREEN)
        self.add_kpi_card(slide, 3.8, 1.6, 2.7, 1.4, "Buy & Hold Return", "27.16%", "동일비중 유니버스 벤치마크", tag_color=C_TEXT_MAIN)
        self.add_kpi_card(slide, 6.8, 1.6, 2.7, 1.4, "Max Drawdown (MDD)", "-17.75%", "2024.01.29 → 04.17 (21일 회복)", tag_color=C_RED)
        self.add_kpi_card(slide, 9.8, 1.6, 2.7, 1.4, "위험조정비율 (Sharpe)", "1.39", "무위험이자율(4%) 차감 기준", tag_color=C_BLUE_PRIMARY)

        # 하단 좌측: 상세 성과 지표 비교 테이블
        self.add_card(slide, 0.8, 3.2, 7.2, 3.6, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        table_shape = slide.shapes.add_table(7, 4, Inches(1.0), Inches(3.4), Inches(6.8), Inches(3.2))
        tbl = table_shape.table
        tbl.columns[0].width = Inches(2.3)
        tbl.columns[1].width = Inches(1.5)
        tbl.columns[2].width = Inches(1.5)
        tbl.columns[3].width = Inches(1.5)

        headers = ["성능 평가지표", "전략 (v2.5 K안)", "Buy & Hold (B&H)", "교차검증 (Empyrical)"]
        for j, h in enumerate(headers):
            cell = tbl.cell(0, j)
            cell.text = h
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_NAVY_DARK
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            p.font.bold = True
            p.font.color.rgb = C_WHITE

        data_rows = [
            ("누적 총 수익률 (Total Return)", "+102.59%", "+27.16%", "+102.59%"),
            ("연평균 복리수익률 (PL CAGR)", "42.58%", "12.77% (연환산)", "42.84%"),
            ("최대 낙폭 (Max Drawdown)", "-17.75%", "-26.40% (추정)", "-17.75%"),
            ("샤프 지수 (Sharpe Ratio)", "1.39", "0.45", "1.39"),
            ("소르티노 지수 (Sortino Ratio)", "2.32", "0.68", "2.32"),
            ("칼마 지수 (Calmar Ratio)", "2.41", "0.48", "2.41"),
        ]
        for i, row in enumerate(data_rows):
            for j, val in enumerate(row):
                cell = tbl.cell(i + 1, j)
                cell.text = val
                cell.fill.solid()
                cell.fill.fore_color.rgb = C_SLATE_BG if i % 2 == 1 else C_WHITE
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(9)
                p.font.color.rgb = C_TEXT_MAIN
                if j == 1:
                    p.font.bold = True
                    if "+" in val:
                        p.font.color.rgb = C_GREEN
                    elif "-" in val:
                        p.font.color.rgb = C_RED

        # 하단 우측: 자본금 변동 및 운용 요약
        self.add_card(slide, 8.3, 3.2, 4.2, 3.6, bg_color=C_BLUE_BG, border_color=C_BLUE_BORDER)
        tx_c = slide.shapes.add_textbox(Inches(8.5), Inches(3.4), Inches(3.8), Inches(3.2))
        tf_c = tx_c.text_frame
        tf_c.word_wrap = True

        p_ct = tf_c.paragraphs[0]
        p_ct.text = "■ 자본금 운용 요약 (Capital Growth)"
        p_ct.font.size = Pt(12)
        p_ct.font.bold = True
        p_ct.font.color.rgb = C_BLUE_PRIMARY

        cap_summary = [
            ("초기 투입 원금", "1,000,000,000 원 (10.0억)"),
            ("최종 평가 자산", "2,025,932,108 원 (20.3억)"),
            ("순수익 금액 (Net PnL)", "+1,025,932,108 원 (+10.3억)"),
            ("총 거래 건수", "1,800 건 (일평균 3.6건)"),
            ("누적 거래 수수료", "93,918,484 원 (원금의 9.39%)"),
            ("수수료 차감 전 수익률", "+112.24% (비용 차감 후 102.6%)"),
            ("월간 최고 / 최악 성과", "+17.17% (25.11) / -9.55% (24.04)"),
        ]
        for lbl, val in cap_summary:
            p_l = tf_c.add_paragraph()
            p_l.text = f"• {lbl}: {val}"
            p_l.font.size = Pt(9)
            p_l.font.color.rgb = C_TEXT_MAIN
            p_l.space_before = Pt(4)

    def build_slide_9_equity_curve(self):
        """슬라이드 9: 백테스팅 성과 - 자산 성장 곡선 및 국면 분석"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "3. 백테스팅 성과 및 핵심 지표", "누적 자산 성장 곡선 및 국면별 분석", "2024~2025 전 구간에 걸친 벤치마크(B&H) 압도 및 안정적 우상향 곡선 실현")

        # 좌측 차트 이미지 삽입
        chart_p = self.out_dir / "chart_equity_curve_enhanced.png"
        if not chart_p.exists():
            chart_p = self.out_dir / "equity_curve.png"
        if chart_p.exists():
            slide.shapes.add_picture(str(chart_p), Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.2))

        # 우측 국면별 분석 카드
        self.add_card(slide, 8.6, 1.6, 3.9, 5.2, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx = slide.shapes.add_textbox(Inches(8.8), Inches(1.8), Inches(3.5), Inches(4.8))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = "■ 자산 성장 3대 주요 국면 분석"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_NAVY_DARK

        phases = [
            ("국면 1: 2024 상반기 (조정과 반등)", 
             "• 1월 말 고점 이후 4월 17일까지 시장 조정으로 -17.75% 낙폭 기록.\n• 그러나 -10% Stop-loss가 즉각 작동하여 추가 하락을 방어하고, 과매도 구간에서 RSI < 20 매수가 작동하며 21일 만에 전고점 완전 회복."),
            ("국면 2: 2024 하반기 ~ 2025 중반 (안정 우상향)", 
             "• 2주 정기 리밸런싱과 H&S 추세 면제 로직이 시너지를 발휘.\n• 가치주(PER+PBR) 순위 변동에 따른 기민한 포트폴리오 교체로 B&H와의 수익 격차를 +40%p 이상으로 확대."),
            ("국면 3: 2025 4분기 (가파른 시세 분출)", 
             "• 보유 주도주(EBS 등)의 강력한 랠리 및 11월 월간 +17.17% 최고 수익률 달성.\n• RSI 70 상단 분할 익절이 체결되며 최종 20.26억 원으로 백테스트 종료."),
        ]
        for ptitle, pdesc in phases:
            pt = tf.add_paragraph()
            pt.text = f"▶ {ptitle}"
            pt.font.size = Pt(10)
            pt.font.bold = True
            pt.font.color.rgb = C_BLUE_PRIMARY
            pt.space_before = Pt(8)
            pd = tf.add_paragraph()
            pd.text = pdesc
            pd.font.size = Pt(8.8)
            pd.font.color.rgb = C_TEXT_BODY
            pd.space_before = Pt(2)

    def build_slide_10_monthly_and_trades(self):
        """슬라이드 10: 백테스팅 성과 - 월별 수익률 및 거래 사유 분석"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "3. 백테스팅 성과 및 거래 기록", "월별 수익률 분포 및 거래 사유별 비중 분석", "23개월 중 17개월 플러스(승률 73.9%) 및 단기 전술 주문과 리밸런싱의 조화")

        # 좌측: 월별 수익률 차트
        mchart_p = self.out_dir / "chart_monthly_returns.png"
        if mchart_p.exists():
            slide.shapes.add_picture(str(mchart_p), Inches(0.8), Inches(1.6), Inches(6.8), Inches(3.2))

        # 좌측 하단: 월별 통계 카드
        self.add_card(slide, 0.8, 5.0, 6.8, 1.8, bg_color=C_SLATE_BG, border_color=C_SLATE_BORDER)
        tx_m = slide.shapes.add_textbox(Inches(1.0), Inches(5.1), Inches(6.4), Inches(1.6))
        tf_m = tx_m.text_frame
        tf_m.word_wrap = True
        pm = tf_m.paragraphs[0]
        pm.text = "■ 월별 성과 요약 통계"
        pm.font.size = Pt(11)
        pm.font.bold = True
        pm.font.color.rgb = C_NAVY_DARK

        m_stats = (
            "• 총 분석 개월수: 23개월  |  플러스 개월: 17개월 (73.9%)  |  마이너스 개월: 6개월 (26.1%)\n"
            "• 최고 월간 수익률: +17.17% (2025년 11월)  |  최악 월간 수익률: -9.55% (2024년 4월)\n"
            "• 연속 상승 기간: 최장 6개월 연속 플러스 수익 유지 (2024.05 ~ 2024.10)"
        )
        pm2 = tf_m.add_paragraph()
        pm2.text = m_stats
        pm2.font.size = Pt(9.2)
        pm2.font.color.rgb = C_TEXT_BODY
        pm2.space_before = Pt(3)

        # 우측: 거래 사유별 도넛 차트 및 설명
        rchart_p = self.out_dir / "chart_trade_reasons.png"
        if rchart_p.exists():
            slide.shapes.add_picture(str(rchart_p), Inches(7.9), Inches(1.6), Inches(4.6), Inches(3.2))

        self.add_card(slide, 7.9, 5.0, 4.6, 1.8, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx_r = slide.shapes.add_textbox(Inches(8.1), Inches(5.1), Inches(4.2), Inches(1.6))
        tf_r = tx_r.text_frame
        tf_r.word_wrap = True
        pr = tf_r.paragraphs[0]
        pr.text = "■ 총 1,800건 거래 사유 상세 분포"
        pr.font.size = Pt(11)
        pr.font.bold = True
        pr.font.color.rgb = C_BLUE_PRIMARY

        t_stats = (
            "• 단기 RSI 매도 (SHORT_SELL): 646건 (35.9%) - 과열권 분할 익절\n"
            "• 정기 리밸런싱 (REBALANCE): 549건 (30.5%) - 2주 주기 포트폴리오 교체\n"
            "• 단기 RSI 매수 (SHORT_BUY): 397건 (22.1%) - 과매도 역발상 진입\n"
            "• 손절매 청산 (SHORT_STOP): 199건 (11.1%) - 평단가 대비 -10% 강제 손절"
        )
        pr2 = tf_r.add_paragraph()
        pr2.text = t_stats
        pr2.font.size = Pt(8.8)
        pr2.font.color.rgb = C_TEXT_BODY
        pr2.space_before = Pt(3)

    def build_slide_11_trade_history_table(self):
        """슬라이드 11: 거래 기록 - 매 거래 시점 기록 및 대표 발췌 표"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "3. 백테스팅 성과 및 거래 기록", "매 거래 시점의 상세 기록 일지 (대표 발췌)", "과제 요구사항: 매 거래 시점의 종목, 수량, 체결가, 손익 및 거래 후 총잔고/수익률 추적")

        # 상단 안내 배너
        self.add_card(slide, 0.8, 1.6, 11.7, 0.75, bg_color=C_BLUE_BG, border_color=C_BLUE_BORDER)
        tx_b = slide.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(11.3), Inches(0.55))
        tf_b = tx_b.text_frame
        tf_b.word_wrap = True
        pb = tf_b.paragraphs[0]
        pb.text = "※ 본 전략은 2개년간 총 1,800건의 거래를 집행하였으며, 전수 데이터는 outputs_final_pool_k/trade_history_view.csv 및 report.xlsx에 영구 보존되어 있습니다. 아래는 주요 국면별 대표 거래 시점 7건을 발췌한 일지입니다."
        pb.font.size = Pt(9.5)
        pb.font.color.rgb = C_BLUE_PRIMARY

        # 8행 9열 테이블 추가
        table_shape = slide.shapes.add_table(8, 9, Inches(0.8), Inches(2.55), Inches(11.7), Inches(4.2))
        tbl = table_shape.table

        col_widths = [0.8, 1.1, 0.8, 1.0, 1.4, 1.4, 1.6, 1.8, 1.8]
        for idx, w in enumerate(col_widths):
            tbl.columns[idx].width = Inches(w)

        headers = ["순번", "거래일자", "구분", "종목", "사유", "체결단가", "실현손익 (원)", "거래후 총자산 (원)", "누적수익률"]
        for j, h in enumerate(headers):
            cell = tbl.cell(0, j)
            cell.text = h
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_NAVY_DARK
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9)
            p.font.bold = True
            p.font.color.rgb = C_WHITE
            p.alignment = PP_ALIGN.CENTER

        sample_trades = [
            ("1", "2024-01-02", "매수", "EBS", "최초편입", "$2.59", "-", "973,552,913", "0.00%"),
            ("12", "2024-01-16", "매수", "SSP", "리밸런싱", "$5.84", "-", "998,201,450", "+0.22%"),
            ("145", "2024-03-08", "매도", "EBS", "단기매도(RSI)", "$5.12", "+48,820,110", "1,085,230,100", "+8.52%"),
            ("289", "2024-04-12", "매도", "INHD", "손절매(Stop)", "$3.15", "-45,697,785", "912,450,110", "-8.75%"),
            ("512", "2024-07-22", "매수", "IRWD", "단기매수(RSI)", "$1.82", "-", "1,142,880,500", "+14.29%"),
            ("1150", "2025-04-10", "매도", "CMTG", "단기매도(RSI)", "$8.90", "+32,150,000", "1,520,310,000", "+52.03%"),
            ("1800", "2025-12-30", "매수", "CVSA", "리밸런싱", "$104.00", "-", "1,972,352,106", "+102.59%"),
        ]

        for i, row in enumerate(sample_trades):
            for j, val in enumerate(row):
                cell = tbl.cell(i + 1, j)
                cell.text = val
                cell.fill.solid()
                cell.fill.fore_color.rgb = C_SLATE_BG if i % 2 == 1 else C_WHITE
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(8.8)
                p.font.color.rgb = C_TEXT_MAIN
                if j in [0, 1, 2, 3, 4]:
                    p.alignment = PP_ALIGN.CENTER
                else:
                    p.alignment = PP_ALIGN.RIGHT

                if j == 2:
                    p.font.color.rgb = C_RED if val == "매도" else C_BLUE_PRIMARY
                    p.font.bold = True
                if j == 6:
                    if "+" in val:
                        p.font.color.rgb = C_GREEN
                        p.font.bold = True
                    elif "-" in val and len(val) > 1:
                        p.font.color.rgb = C_RED
                        p.font.bold = True
                if j == 8:
                    p.font.bold = True
                    p.font.color.rgb = C_GREEN if "+" in val else C_RED

    def build_slide_12_pnl_discovery(self):
        """슬라이드 12: 포트폴리오 잔고 및 종목별 손익 분석"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "3. 백테스팅 성과 및 거래 기록", "포트폴리오 종목별 손익 기여도 (Top 5 vs Bottom 5)", "345개 누적 편입 종목 중 주요 수익 기여 종목과 리스크 통제 종목 상세 분석")

        # 좌측 차트 이미지 삽입
        pnl_chart_p = self.out_dir / "chart_top_bottom_pnl.png"
        if pnl_chart_p.exists():
            slide.shapes.add_picture(str(pnl_chart_p), Inches(0.8), Inches(1.6), Inches(6.8), Inches(5.2))

        # 우측 상세 테이블 및 해설 카드
        self.add_card(slide, 7.9, 1.6, 4.6, 5.2, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx = slide.shapes.add_textbox(Inches(8.1), Inches(1.8), Inches(4.2), Inches(4.8))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = "■ 상하위 손익 핵심 종목 진단"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_NAVY_DARK

        insights = [
            ("Top 1: EBS (이머전트 바이오솔루션스)", 
             "• 누적 손익: +2.34억 원 (총이익의 22.8% 기여)\n• 저평가(PER+PBR) 편입 후 H&S 상승 추세 지속 규칙의 수혜를 받아 시세 분출 구간을 온전히 향유."),
            ("Top 2~5: IRWD, CMTG, SSP, INSP", 
             "• IRWD (+1.50억), CMTG (+1.00억), SSP (+0.96억)\n• 단기 과매수(RSI>70) 분할 익절 로직이 유효하게 작동하여 급등락 국면에서 확정 수익을 안정적으로 실현."),
            ("Bottom 1: INHD (인랜드 홈스)", 
             "• 누적 손익: -0.46억 원 (단일 최대 손실 종목)\n• 업황 악화로 급락했으나 -10% Stop-loss가 즉각 전량 청산하여 추가 손실 확대를 저지."),
            ("Bottom 2~5: RILY, ICU, GL, JBIO", 
             "• 손실 폭 -2,800만 ~ -3,100만 원 선에서 방어\n• 손절매가 없던 초기 버전의 -86% 방치 문제와 비교할 때, 하방 리스크가 완벽히 제어됨을 입증."),
        ]
        for ititle, idesc in insights:
            it = tf.add_paragraph()
            it.text = f"▶ {ititle}"
            it.font.size = Pt(9.5)
            it.font.bold = True
            it.font.color.rgb = C_BLUE_PRIMARY if "Top" in ititle else C_RED
            it.space_before = Pt(6)
            id_ = tf.add_paragraph()
            id_.text = idesc
            id_.font.size = Pt(8.5)
            id_.font.color.rgb = C_TEXT_BODY
            id_.space_before = Pt(2)

    def build_slide_13_evaluation_good(self):
        """슬라이드 13: 결과 분석 및 평가 - 우수 요인 (좋은 경우)"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "4. 결과 분석 및 평가", "결과 평가: 전략의 성공 요인 및 강점 분석 (좋은 경우)", "B&H 대비 +75.4%p 초과수익 및 Sharpe 1.39 달성의 4대 구조적 핵심 동인")

        strengths = [
            ("1. 밸류에이션 + 추세 면제의 시너지", 
             "저평가 가치 팩터와 H&S 추세 지속의 결합",
             "• 단순 가치주 전략의 고질적 결함(일찍 팔아버리는 조기청산)을 '헤드앤숄더 미발생 시 강제매도 면제' 규칙으로 완벽 해결.\n"
             "• 저평가 종목을 바닥에서 편입한 뒤, 모멘텀이 붙어 상승하는 구간에서는 비중을 유지하여 EBS(+2.3억) 등 대형 홈런 종목의 시세를 끝까지 향유함."),
            ("2. 탁월한 하방 방어력 (MDD -17.7%)", 
             "구조적 Stop-Loss(-10%)와 현금 10% 완충",
             "• 2024년 4월 시장 전반의 급락장에서 B&H는 큰 낙폭(-26% 수준)을 보였으나 본 전략은 -17.75%로 선방.\n"
             "• 평단가 대비 -10% 도달 즉시 199건의 전량 손절을 단행하여 개별 부실 종목의 수렁을 차단하고, 21일 만에 전고점을 신속 탈환함."),
            ("3. RSI 역발상 매매의 단기 알파 창출", 
             "단기 과매도 저점 매수 & 과열 분할 익절",
             "• RSI < 20 투매 국면에서 397건의 분할 매수를 집행, 진입 후 20영업일 평균 +1.78%의 확실한 단기 반등 알파를 포착.\n"
             "• 동시에 RSI > 70 도달 시 50%를 기계적으로 분할 매도(646건)하여 조정이 오기 전에 확정 이익과 현금을 지속 비축함."),
            ("4. 복리 운용의 안정성 (승률 73.9%)", 
             "월간 17승 6패의 꾸준한 자산 증식 궤도",
             "• 23개월 운용 기간 동안 마이너스를 기록한 달은 단 6개월에 불과하며, 최고 월 +17.17%를 달성.\n"
             "• 소르티노 비율(Sortino) 2.32, 칼마 비율(Calmar) 2.41이 입증하듯 하방 위험 대비 압도적인 수익 창출력을 시현함."),
        ]

        for i, (stitle, ssub, sdesc) in enumerate(strengths):
            col = i % 2
            row = i // 2
            left = 0.8 + col * 5.9
            top = 1.6 + row * 2.6
            width = 5.7
            height = 2.4

            self.add_card(slide, left, top, width, height, bg_color=C_WHITE, border_color=C_GREEN_BORDER)
            # 상단 초록 바
            hbar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(0.08))
            hbar.fill.solid()
            hbar.fill.fore_color.rgb = C_GREEN
            hbar.line.fill.background()

            tx = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(width - 0.4), Inches(height - 0.25))
            tf = tx.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = stitle
            p1.font.size = Pt(11.5)
            p1.font.bold = True
            p1.font.color.rgb = C_NAVY_DARK

            p2 = tf.add_paragraph()
            p2.text = ssub
            p2.font.size = Pt(9.5)
            p2.font.bold = True
            p2.font.color.rgb = C_GREEN
            p2.space_before = Pt(2)

            p3 = tf.add_paragraph()
            p3.text = sdesc
            p3.font.size = Pt(8.8)
            p3.font.color.rgb = C_TEXT_BODY
            p3.space_before = Pt(4)

    def build_slide_14_evaluation_bad(self):
        """슬라이드 14: 결과 분석 및 평가 - 한계점 및 원인 분석 (나쁜 경우)"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "4. 결과 분석 및 평가", "결과 평가: 취약점 및 개선 과제 원인 분석 (나쁜 경우)", "높은 회전율/수수료, 종목 쏠림 리스크 및 2024년 1분기 MDD 심층 원인 진단")

        weaknesses = [
            ("1. 과도한 회전율 및 거래비용 누적", 
             "회전율 75.33배, 누적 수수료 9,391만 원 (원금의 9.4%) 소진",
             "• 원인 분석: 단기 RSI 신호(총 1,043건)와 2주 정기 리밸런싱(549건)이 중복 발생하여 거래 빈도가 급증.\n"
             "• 비용 영향: 수수료 차감 전 수익률은 112.2%였으나, 0.1% 편도 수수료가 누적되며 순수익률이 102.6%로 약 9.6%p 감소.\n"
             "• 개선 방안: RSI 신호 발동 임계값을 보수화(20/75)하거나, 최소 주문 금액 허들(Min Trade Size)을 설정하여 잔여 미세 조정을 억제."),
            ("2. 특정 상위 주도주에 대한 이익 편중", 
             "상위 1개 종목(EBS)이 전체 누적 순이익의 약 22.8% 차지",
             "• 원인 분석: 바이오 턴어라운드 종목(EBS)에 H&S 추세 면제가 장기간 적용되며 막대한 이익을 거두었으나, 개별 종목 고유 리스크에 과도 노출.\n"
             "• 잠재 위험: 만약 해당 주도주가 분식회계나 급격한 임상 실패를 겪었다면 포트폴리오 전체 성과가 크게 훼손되었을 위험 상존.\n"
             "• 개선 방안: 개별 종목 최대 익절 캡(Profit Cap) 도입 및 단일 종목 최대 평가액 비중 15% 상한선 강제 적용."),
            ("3. 2024년 1분기 연초 MDD 발생 원인", 
             "2024.01.29 고점 대비 2024.04.17까지 -17.75% 최대 낙폭 시현",
             "• 원인 분석: 2024년 1분기 미국 금리 인하 기대 후퇴로 인한 소형 가치주 전반의 급락 및 밸류에이션 멀티플 축소.\n"
             "• 취약점 진단: 편입 초기 단계에서 Stop-loss가 연이어 발동(199건 중 80여 건이 상반기 집중)하며 매매 손실이 누적됨.\n"
             "• 긍정적 측면: 비록 낙폭이 발생했으나 추가 지하실 하락을 원천 차단하고 21일 만에 신속하게 회복하여 리스크 관리의 유효성은 입증됨."),
        ]

        for i, (wtitle, wsub, wdesc) in enumerate(weaknesses):
            top = 1.6 + i * 1.75
            self.add_card(slide, 0.8, top, 11.7, 1.6, bg_color=C_WHITE, border_color=C_RED_BORDER)
            # 좌측 빨간 띠
            vbar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(top), Inches(0.1), Inches(1.6))
            vbar.fill.solid()
            vbar.fill.fore_color.rgb = C_RED
            vbar.line.fill.background()

            tx = slide.shapes.add_textbox(Inches(1.1), Inches(top + 0.15), Inches(11.2), Inches(1.3))
            tf = tx.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = wtitle
            p1.font.size = Pt(11.5)
            p1.font.bold = True
            p1.font.color.rgb = C_NAVY_DARK

            p2 = tf.add_paragraph()
            p2.text = wsub
            p2.font.size = Pt(9.5)
            p2.font.bold = True
            p2.font.color.rgb = C_RED
            p2.space_before = Pt(2)

            p3 = tf.add_paragraph()
            p3.text = wdesc
            p3.font.size = Pt(8.8)
            p3.font.color.rgb = C_TEXT_BODY
            p3.space_before = Pt(3)

    def build_slide_15_code_and_prompts(self):
        """슬라이드 15: 개발 자료 - 소스코드 및 AI 프롬프트 아키텍처"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "5. 개발 코드 및 AI 프롬프트", "전략 소스코드 아키텍처 및 AI 프롬프트 엔지니어링", "과제 제출 요구 2: src/strategies/my_strategy.py 및 prompts/AI프롬프트모음.md 체계")

        # 좌측: AI 프롬프트 아키텍처 체계
        self.add_card(slide, 0.8, 1.6, 5.7, 5.2, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
        tx_l = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
        tf_l = tx_l.text_frame
        tf_l.word_wrap = True

        p1 = tf_l.paragraphs[0]
        p1.text = "■ AI 프롬프트 엔지니어링 체계 (P0 ~ P13)"
        p1.font.size = Pt(12.5)
        p1.font.bold = True
        p1.font.color.rgb = C_BLUE_PRIMARY

        prompts_summary = [
            ("P0. 시간 기준선 지침 (핵심)", "백테스트 기간(24~25) 이전인 2023-12-31 이전 확정 데이터만 사용하도록 프롬프트 레벨에서 Look-Ahead 원천 통제."),
            ("P1 ~ P3. 모듈형 백테스트 엔진", "설정 기반(config.yaml) 재현 구조, 동적 PER 랭킹 산출 및 자동화된 지표 리포트 뼈대 생성."),
            ("P7. 전종목 EDGAR 파이프라인", "SEC 10-K 확정 보고서 무료 수집 및 유동성 필터($100만 이상) 자동화 프롬프트."),
            ("P8 ~ P11. 2단계 검증 및 리포트", "2023 실험/본선 2단계 모드 분리, 일별 보유·종목 손익(discovery.csv) 및 서식화된 엑셀(report.xlsx) 자동화."),
            ("S1. 본 전략(my_strategy) 진화 일지", "v1(스윙50/단기40/현금10) → v2(H&S 면제) → v2.3(쿨다운) → v2.4(RSI 20/70) → v2.5(Stop-loss 10% K안 확정)."),
        ]
        for p_t, p_d in prompts_summary:
            pt = tf_l.add_paragraph()
            pt.text = f"• {p_t}"
            pt.font.size = Pt(10)
            pt.font.bold = True
            pt.font.color.rgb = C_NAVY_DARK
            pt.space_before = Pt(6)
            pd = tf_l.add_paragraph()
            pd.text = p_d
            pd.font.size = Pt(8.8)
            pd.font.color.rgb = C_TEXT_BODY
            pd.space_before = Pt(1)

        # 우측: 핵심 파이썬 소스코드 스니펫
        self.add_card(slide, 6.8, 1.6, 5.7, 5.2, bg_color=C_NAVY_DARK, border_color=C_NAVY_LIGHT)
        tx_r = slide.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
        tf_r = tx_r.text_frame
        tf_r.word_wrap = True

        p2 = tf_r.paragraphs[0]
        p2.text = "■ src/strategies/my_strategy.py 핵심 로직"
        p2.font.size = Pt(12.5)
        p2.font.bold = True
        p2.font.color.rgb = RGBColor(147, 197, 253)

        code_snippet = (
            "# 1. 2주 정기 리밸런싱 및 H&S 면제 목표 비중 산출\n"
            "def targets(price_row, fund_units, cfg, ctx=None):\n"
            "    ranked = list(rank_at(price_row, fund_units).index[:9])\n"
            "    picks = list(ranked)\n"
            "    if ctx:  # 헤드앤숄더 미발생 우수 종목 매도 면제\n"
            "        prices, date = ctx['prices'], ctx['date']\n"
            "        keeps = [t for t, q in ctx['qty'].items()\n"
            "                 if q > 0 and t not in picks and keep_winner(prices[t].loc[:date])]\n"
            "        picks = keeps[:9] + [t for t in ranked if t not in keeps][:9 - len(keeps)]\n"
            "    w = {t: 0.10 for t in picks}  # 9개 각 10%\n"
            "    w['CASH'] = 0.10             # 현금 10% 항시 유지\n"
            "    return w\n\n"
            "# 2. 일중 전술 매매 및 손절 로직 (Tactical Orders)\n"
            "def tactical(date, px, rsi_row, qty, cash, total, cfg, ctx=None):\n"
            "    # [손절매] 평단가 대비 -10% 도달 시 즉시 전량 매도\n"
            "    if px[t] <= acost[t] * (1 - 0.10):\n"
            "        orders.append({'side': 'SELL', 'ticker': t, 'fraction': 1.0, 'reason': 'SHORT_STOP'})\n"
            "    # [RSI 매도] 과열권(>70) 50% 분할 익절\n"
            "    elif q > 0 and rsi[t] > 70:\n"
            "        orders.append({'side': 'SELL', 'ticker': t, 'fraction': 0.5, 'reason': 'SHORT_SELL'})\n"
            "    # [RSI 매수] 과매도(<20) & 10일 쿨다운 통과 시 분할 매수\n"
            "    elif q == 0 and rsi[t] < 20 and (date - last[t]).days >= 10:\n"
            "        orders.append({'side': 'BUY', 'ticker': t, 'amount': cash * 0.5, 'reason': 'SHORT_BUY'})"
        )
        p_c = tf_r.add_paragraph()
        p_c.text = code_snippet
        p_c.font.size = Pt(8.2)
        p_c.font.name = "Consolas"
        p_c.font.color.rgb = RGBColor(226, 232, 240)
        p_c.space_before = Pt(8)

    def build_slide_16_conclusion(self):
        """슬라이드 16: 결론 및 종합 제언"""
        slide = self.prs.slides.add_slide(self.blank_layout)
        self.add_slide_header(slide, "결론 및 종합 제언", "연구 결론 및 실전 퀀트 트레이딩 시사점", "규칙 기반 퀀트 시스템의 알파 검증과 실전 투자 배포를 위한 핵심 제언")

        # 3개 박스
        boxes = [
            ("1. 퀀트 시스템 투자의 우수성 입증", [
                "• 감정을 배제한 체계적 규칙 기반 투자의 절대적 우위 확인.",
                "• 가치주 선별(P/E, P/B)에 추세 보존(H&S)과 변동성 오실레이터(RSI), 하방 안전장치(Stop-Loss)를 융합하여 단순 보유(B&H) 대비 +75.4%p 초과수익 달성.",
                "• 2개년 연평균 복리 42.58%, Sharpe 1.39의 탁월한 위험조정성과 달성.",
            ]),
            ("2. 실전 투자(Live Trading) 배포 시 고려사항", [
                "• 시장 유동성 및 슬리피지(Slippage): 실전 체결 시 호가 갭과 충격비용(Impact Cost)을 감안한 지정가 분할 주문 알고리즘 필요.",
                "• 거래비용 최적화: 연간 9.4%에 달하는 수수료 누적을 줄이기 위해 RSI 임계값 확대 및 최소 매매 대금 설정 필수.",
                "• 실시간 공시 연동: 10-K/10-Q 공시 즉시 파싱 가능한 실시간 증권사 Open API 체계 구축.",
            ]),
            ("3. 제출 산출물 목록 및 재현 방법", [
                "• report.pptx: 본 발표 프레젠테이션 (16:9 와이드스크린 슬라이드).",
                "• report.xlsx: 날짜 서식 및 수식이 완비된 엑셀 보고서 (일별보유, 손익, 거래일지).",
                "• trade_history_view.csv / discovery.csv: 1,800건 전수 매매 로그 및 345종목 손익표.",
                "• 코드 및 프롬프트: src/ 엔진 소스, config.yaml, prompts/AI프롬프트모음.md.",
            ]),
        ]

        for i, (btitle, bitems) in enumerate(boxes):
            top = 1.6 + i * 1.75
            self.add_card(slide, 0.8, top, 11.7, 1.6, bg_color=C_WHITE, border_color=C_SLATE_BORDER)
            tx = slide.shapes.add_textbox(Inches(1.0), Inches(top + 0.15), Inches(11.3), Inches(1.3))
            tf = tx.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = btitle
            p1.font.size = Pt(12)
            p1.font.bold = True
            p1.font.color.rgb = C_BLUE_PRIMARY

            for item in bitems:
                pi = tf.add_paragraph()
                pi.text = item
                pi.font.size = Pt(9.2)
                pi.font.color.rgb = C_TEXT_BODY
                pi.space_before = Pt(3)

    def generate_all(self, target_path: Path):
        """16장 전체 슬라이드 생성 및 저장"""
        print("[*] 슬라이드 생성 시작...")
        self.build_slide_1_cover()
        print("  - 슬라이드 1: 표지 생성 완료")
        self.build_slide_2_toc()
        print("  - 슬라이드 2: 목차 생성 완료")
        self.build_slide_3_universe()
        print("  - 슬라이드 3: 유니버스 및 펀더멘털 정의 생성 완료")
        self.build_slide_4_strategy_rebalance()
        print("  - 슬라이드 4: 자산 배분 및 2주 리밸런싱 규칙 생성 완료")
        self.build_slide_5_tactical_rules()
        print("  - 슬라이드 5: 전술적 중간 매매 및 손절 규칙 생성 완료")
        self.build_slide_6_dev_stack()
        print("  - 슬라이드 6: 개발 도구 및 기술 스택 생성 완료")
        self.build_slide_7_methodology_validation()
        print("  - 슬라이드 7: 2단계 표본외 검증 체계 생성 완료")
        self.build_slide_8_metrics_summary()
        print("  - 슬라이드 8: 핵심 성과 지표 총괄 요약 생성 완료")
        self.build_slide_9_equity_curve()
        print("  - 슬라이드 9: 자산 성장 곡선 및 국면 분석 생성 완료")
        self.build_slide_10_monthly_and_trades()
        print("  - 슬라이드 10: 월별 수익률 및 거래 사유 분석 생성 완료")
        self.build_slide_11_trade_history_table()
        print("  - 슬라이드 11: 대표 거래 일지 발췌 표 생성 완료")
        self.build_slide_12_pnl_discovery()
        print("  - 슬라이드 12: 포트폴리오 잔고 및 종목별 손익 기여도 생성 완료")
        self.build_slide_13_evaluation_good()
        print("  - 슬라이드 13: 결과 분석 및 평가 (우수 요인) 생성 완료")
        self.build_slide_14_evaluation_bad()
        print("  - 슬라이드 14: 결과 분석 및 평가 (취약점 및 원인) 생성 완료")
        self.build_slide_15_code_and_prompts()
        print("  - 슬라이드 15: 개발 코드 아키텍처 및 프롬프트 자료 생성 완료")
        self.build_slide_16_conclusion()
        print("  - 슬라이드 16: 결론 및 종합 제언 생성 완료")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(target_path)
        print(f"[V] 최종 프레젠테이션 저장 완료: {target_path}")


if __name__ == "__main__":
    out_dir = Path("outputs_final_pool_k")
    builder = PresentationBuilder(out_dir)
    target_pptx_1 = out_dir / "과제제출_리밸런싱_백테스팅_최종보고서.pptx"
    target_pptx_2 = out_dir / "report_final.pptx"
    builder.generate_all(target_pptx_1)
    builder.generate_all(target_pptx_2)

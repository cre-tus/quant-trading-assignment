"""슬라이드용 고해상도 시각화 차트 생성 스크립트."""
from pathlib import Path
import json
import sys
sys.path.insert(0, ".")
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 폰트 설정 (Windows 한글 지원: Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

out_dir = Path("outputs_final_pool_k")

# 1. 월별 수익률 차트 생성
eq = pd.read_csv(out_dir / "daily_equity.csv", index_col=0, parse_dates=True)
monthly_eq = eq["total"].resample("ME").last()
monthly_ret = monthly_eq.pct_change().dropna()

fig, ax = plt.subplots(figsize=(10, 4.2), dpi=200)
colors = ['#10B981' if r >= 0 else '#EF4444' for r in monthly_ret]
bars = ax.bar(monthly_ret.index.strftime('%Y-%m'), monthly_ret.values * 100, color=colors, width=0.6, edgecolor='none', zorder=3)
ax.axhline(0, color='#64748B', linewidth=0.8, linestyle='--')
ax.grid(axis='y', alpha=0.3, zorder=0)
ax.set_ylabel('월간 수익률 (%)', fontsize=11, fontweight='bold', color='#1E293B')
ax.set_title('전략 월별 수익률 추이 (2024.01 ~ 2025.12)', fontsize=13, fontweight='bold', color='#0F172A', pad=12)
plt.xticks(rotation=45, ha='right', fontsize=9, color='#475569')
plt.yticks(fontsize=9, color='#475569')

# 상단 수치 표기 (최고/최악 강조)
max_idx = np.argmax(monthly_ret.values)
min_idx = np.argmin(monthly_ret.values)
for i, bar in enumerate(bars):
    val = monthly_ret.values[i] * 100
    if i == max_idx:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6, f"+{val:.1f}%\n(최고)", 
                ha='center', va='bottom', fontsize=8, fontweight='bold', color='#059669')
    elif i == min_idx:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 2.5, f"{val:.1f}%\n(최악)", 
                ha='center', va='top', fontsize=8, fontweight='bold', color='#DC2626')

plt.tight_layout()
fig.savefig(out_dir / "chart_monthly_returns.png")
plt.close(fig)
print("[+] chart_monthly_returns.png 생성 완료")

# 2. PnL Top 5 & Bottom 5 기여도 차트 생성
disc = pd.read_csv(out_dir / "discovery.csv")
top5 = disc.sort_values(by="total_pnl", ascending=False).head(5)
bot5 = disc.sort_values(by="total_pnl", ascending=True).head(5)
combined = pd.concat([top5, bot5]).sort_values(by="total_pnl", ascending=True)

fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
pnl_vals_m = combined["total_pnl"].values / 1e8  # 억원 단위
y_labels = [f"{t} ({n})" if n != t else t for t, n in zip(combined["ticker"], combined["name_kr"])]
bar_colors = ['#EF4444' if v < 0 else '#10B981' for v in pnl_vals_m]

bars = ax.barh(y_labels, pnl_vals_m, color=bar_colors, height=0.6, zorder=3)
ax.axvline(0, color='#64748B', linewidth=1, linestyle='-')
ax.grid(axis='x', alpha=0.3, zorder=0)
ax.set_xlabel('누적 손익 (억 원)', fontsize=11, fontweight='bold', color='#1E293B')
ax.set_title('주요 종목별 누적 손익 기여도 (Top 5 vs Bottom 5)', fontsize=13, fontweight='bold', color='#0F172A', pad=12)
plt.yticks(fontsize=9, fontweight='bold', color='#334155')
plt.xticks(fontsize=9, color='#475569')

for bar in bars:
    w = bar.get_width()
    if w >= 0:
        ax.text(w + 0.05, bar.get_y() + bar.get_height()/2, f"+{w:.2f}억", 
                ha='left', va='center', fontsize=8.5, fontweight='bold', color='#065F46')
    else:
        ax.text(w - 0.05, bar.get_y() + bar.get_height()/2, f"{w:.2f}억", 
                ha='right', va='center', fontsize=8.5, fontweight='bold', color='#991B1B')

plt.tight_layout()
fig.savefig(out_dir / "chart_top_bottom_pnl.png")
plt.close(fig)
print("[+] chart_top_bottom_pnl.png 생성 완료")

# 3. 거래 사유별 도넛 차트 생성
with open(out_dir / "analysis.json", "r", encoding="utf-8") as f:
    an = json.load(f)

trade_reasons = an.get("trades_by_reason", {})
# 한글 라벨 매핑
labels_kr = {
    "SHORT_SELL(rsi)": "단기 RSI 분할익절\n(646건, 35.9%)",
    "REBALANCE": "정기 리밸런싱 교체\n(549건, 30.5%)",
    "SHORT_BUY(rsi)": "단기 RSI 과매도매수\n(397건, 22.1%)",
    "SHORT_STOP": "Stop-Loss 손절매\n(199건, 11.1%)",
    "INIT": "최초 편입\n(9건, 0.5%)"
}
labels = [labels_kr.get(k, k) for k in trade_reasons.keys()]
sizes = list(trade_reasons.values())
donut_colors = ['#3B82F6', '#6366F1', '#10B981', '#EF4444', '#94A3B8']

fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                  startangle=140, colors=donut_colors,
                                  textprops=dict(color="#1E293B", fontsize=8.5),
                                  pctdistance=0.75,
                                  wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(8)

ax.set_title('총 1,800건 거래 사유별 비중', fontsize=12, fontweight='bold', color='#0F172A', pad=10)
plt.tight_layout()
fig.savefig(out_dir / "chart_trade_reasons.png")
plt.close(fig)
print("[+] chart_trade_reasons.png 생성 완료")

# 4. 고해상도 자산 곡선 개선 차트 생성
prices_full_path = Path("data/prices_full.csv")
if prices_full_path.exists():
    prices = pd.read_csv(prices_full_path, index_col=0, parse_dates=True)
    universe_pool = [ln.strip().upper() for ln in Path("data/pool_tickers.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    px = prices[[c for c in universe_pool if c in prices.columns]].loc["2024-01-01":"2025-12-31"]
    from src.metrics import buy_and_hold
    bh = buy_and_hold(px, 1000000000)
    
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
    ax.plot(eq.index, eq["total"] / 1e8, label="전략 (v2.5 K안: 2W + RSI 20/70 + 손절10%)", color="#2563EB", linewidth=2.2, zorder=4)
    bh_reindexed = bh.reindex(eq.index).ffill()
    ax.plot(bh_reindexed.index, bh_reindexed.values / 1e8, label="Buy & Hold (동일비중 유니버스 벤치마크)", color="#94A3B8", linewidth=1.5, linestyle="--", zorder=3)
    
    ax.set_title("누적 자산 성장 곡선 (2024.01 ~ 2025.12, 초기 자본 10억)", fontsize=13, fontweight='bold', color='#0F172A', pad=12)
    ax.set_xlabel("거래일", fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylabel("총 자산 (억 원)", fontsize=10, fontweight='bold', color='#334155')
    ax.grid(alpha=0.3, zorder=0)
    ax.legend(frameon=True, facecolor='white', edgecolor='#E2E8F0', fontsize=9.5, loc='upper left')
    
    # 최종값 텍스트 표시
    strat_final = eq['total'].iloc[-1] / 1e8
    bh_final = bh_reindexed.iloc[-1] / 1e8
    ax.scatter([eq.index[-1]], [strat_final], color='#2563EB', s=40, zorder=5)
    ax.scatter([bh_reindexed.index[-1]], [bh_final], color='#64748B', s=30, zorder=5)
    ax.text(eq.index[-1], strat_final + 0.4, f"전략: {strat_final:.2f}억 (+102.6%)", ha='right', fontsize=9, fontweight='bold', color='#1D4ED8')
    ax.text(bh_reindexed.index[-1], bh_final - 0.7, f"B&H: {bh_final:.2f}억 (+27.2%)", ha='right', fontsize=9, fontweight='bold', color='#475569')
    
    # MDD 구간 강조
    ax.axvspan(pd.to_datetime("2024-01-29"), pd.to_datetime("2024-04-17"), color='#FEE2E2', alpha=0.5, label='최대 낙폭 구간 (MDD -17.7%)')
    
    plt.tight_layout()
    fig.savefig(out_dir / "chart_equity_curve_enhanced.png")
    plt.close(fig)
    print("[+] chart_equity_curve_enhanced.png 생성 완료")

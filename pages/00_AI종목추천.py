# ----------------------------
# 1-2. 수익률 & 변동성 분석 순위
# ----------------------------
st.subheader("🏆 종목 분석 순위 (정량 지표)")
st.caption("수익률·변동성·위험대비수익을 함께 비교합니다. (투자 권유 아님)")

analysis_rows = []
for name, returns in return_data.items():
    prices = price_data[name]

    # 일간 수익률 계산
    daily_returns = prices.pct_change().dropna()

    # 누적 수익률(%)
    total_return = float(returns.iloc[-1])

    # 변동성: 일간 수익률의 표준편차 (연율화 → 252 거래일 기준)
    volatility = float(daily_returns.std() * np.sqrt(252) * 100)

    # 위험대비수익 (샤프지수 유사: 수익률 ÷ 변동성)
    risk_adj = total_return / volatility if volatility != 0 else 0

    analysis_rows.append({
        "종목": name,
        "수익률(%)": round(total_return, 2),
        "변동성(%)": round(volatility, 2),
        "위험대비수익": round(risk_adj, 3)
    })

analysis_df = pd.DataFrame(analysis_rows)

# 위험대비수익이 높은 순으로 정렬
analysis_df = analysis_df.sort_values("위험대비수익", ascending=False).reset_index(drop=True)

# 순위 컬럼 추가 (1위부터)
analysis_df.insert(0, "순위", range(1, len(analysis_df) + 1))


# 색상 강조 함수 (수익률용)
def color_value(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    color = "red" if v > 0 else ("blue" if v < 0 else "black")
    return f"color: {color}; font-weight: bold;"


styled_analysis = analysis_df.style
if hasattr(styled_analysis, "map"):
    styled_analysis = styled_analysis.map(color_value, subset=["수익률(%)"])
else:
    styled_analysis = styled_analysis.applymap(color_value, subset=["수익률(%)"])

styled_analysis = styled_analysis.format({
    "수익률(%)": "{:+.2f}",
    "변동성(%)": "{:.2f}",
    "위험대비수익": "{:.3f}"
})

st.dataframe(styled_analysis, use_container_width=True, hide_index=True)

# 간단한 해설
if len(analysis_df) > 0:
    best = analysis_df.iloc[0]
    st.info(
        f"📌 **'{best['종목']}'** 이(가) 선택 기간 동안 "
        f"**위험 대비 수익**이 가장 높았습니다. "
        f"(수익률 {best['수익률(%)']:+.2f}%, 변동성 {best['변동성(%)']:.2f}%)\n\n"
        f"⚠️ 단, 과거 데이터일 뿐 미래 수익을 보장하지 않습니다."
    )

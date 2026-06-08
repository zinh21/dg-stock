import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ----------------------------
# 페이지 설정
# ----------------------------
st.set_page_config(page_title="종목 분석 순위", page_icon="🏆", layout="wide")

st.title("🏆 종목 분석 순위 (정량 지표)")
st.caption("수익률·변동성·위험대비수익을 함께 비교합니다. (투자 권유 아님)")

# ----------------------------
# 종목 사전
# ----------------------------
STOCK_DICT = {
    "🇰🇷 삼성전자": "005930.KS",
    "🇰🇷 SK하이닉스": "000660.KS",
    "🇰🇷 LG에너지솔루션": "373220.KS",
    "🇰🇷 현대차": "005380.KS",
    "🇰🇷 NAVER": "035420.KS",
    "🇰🇷 카카오": "035720.KS",
    "🇺🇸 애플(Apple)": "AAPL",
    "🇺🇸 마이크로소프트(Microsoft)": "MSFT",
    "🇺🇸 엔비디아(NVIDIA)": "NVDA",
    "🇺🇸 테슬라(Tesla)": "TSLA",
    "🇺🇸 아마존(Amazon)": "AMZN",
    "🇺🇸 구글(Alphabet)": "GOOGL",
}

# ----------------------------
# 사이드바 입력
# ----------------------------
st.sidebar.header("⚙️ 분석 설정")

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요",
    options=list(STOCK_DICT.keys()),
    default=["🇰🇷 삼성전자", "🇺🇸 애플(Apple)", "🇺🇸 엔비디아(NVIDIA)"]
)

period_option = st.sidebar.selectbox(
    "분석 기간",
    options=["1개월", "3개월", "6개월", "1년", "3년", "5년"],
    index=3
)

period_map = {
    "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
    "1년": "1y", "3년": "3y", "5년": "5y",
}

# ----------------------------
# 데이터 로딩 함수
# ----------------------------
@st.cache_data(ttl=3600)
def load_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"{ticker} 오류: {e}")
        return pd.DataFrame()

# ----------------------------
# 데이터 준비
# ----------------------------
if not selected_names:
    st.warning("👈 사이드바에서 종목을 1개 이상 선택해주세요.")
    st.stop()

period_code = period_map[period_option]

price_data = {}
return_data = {}

with st.spinner("데이터를 불러오는 중..."):
    for name in selected_names:
        ticker = STOCK_DICT[name]
        df = load_stock_data(ticker, period_code)

        if df.empty or "Close" not in df.columns:
            st.warning(f"⚠️ '{name}' 데이터를 불러올 수 없습니다.")
            continue

        df = df.dropna(subset=["Close"])
        if len(df) < 2:
            st.warning(f"⚠️ '{name}' 데이터가 부족합니다.")
            continue

        price_data[name] = df["Close"]
        start_price = df["Close"].iloc[0]
        return_data[name] = (df["Close"] / start_price - 1) * 100

if not price_data:
    st.error("표시할 데이터가 없습니다. 다른 종목/기간을 선택해주세요.")
    st.stop()

# ----------------------------
# 분석 지표 계산
# ----------------------------
analysis_rows = []
for name, returns in return_data.items():
    prices = price_data[name]
    daily_returns = prices.pct_change().dropna()

    total_return = float(returns.iloc[-1])
    volatility = float(daily_returns.std() * np.sqrt(252) * 100)
    risk_adj = total_return / volatility if volatility != 0 else 0

    analysis_rows.append({
        "종목": name,
        "수익률(%)": round(total_return, 2),
        "변동성(%)": round(volatility, 2),
        "위험대비수익": round(risk_adj, 3)
    })

analysis_df = pd.DataFrame(analysis_rows)
analysis_df = analysis_df.sort_values("위험대비수익", ascending=False).reset_index(drop=True)
analysis_df.insert(0, "순위", range(1, len(analysis_df) + 1))

# ----------------------------
# 색상 강조 & 표시
# ----------------------------
def color_value(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    color = "red" if v > 0 else ("blue" if v < 0 else "black")
    return f"color: {color}; font-weight: bold;"

styled = analysis_df.style
if hasattr(styled, "map"):
    styled = styled.map(color_value, subset=["수익률(%)"])
else:
    styled = styled.applymap(color_value, subset=["수익률(%)"])

styled = styled.format({
    "수익률(%)": "{:+.2f}",
    "변동성(%)": "{:.2f}",
    "위험대비수익": "{:.3f}"
})

st.dataframe(styled, use_container_width=True, hide_index=True)

# ----------------------------
# 해설
# ----------------------------
best = analysis_df.iloc[0]
st.info(
    f"📌 **'{best['종목']}'** 이(가) 선택 기간 동안 "
    f"**위험 대비 수익**이 가장 높았습니다. "
    f"(수익률 {best['수익률(%)']:+.2f}%, 변동성 {best['변동성(%)']:.2f}%)\n\n"
    f"⚠️ 과거 데이터일 뿐 미래 수익을 보장하지 않습니다."
)

st.divider()
st.caption("📌 데이터 출처: Yahoo Finance | 학습용 자료이며 투자 권유가 아닙니다.")

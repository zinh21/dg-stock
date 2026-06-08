import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ----------------------------
# 페이지 기본 설정
# ----------------------------
st.set_page_config(
    page_title="주식 수익률 비교 분석",
    page_icon="📈",
    layout="wide"
)

st.title("📈 한국 & 미국 주요 주식 분석")
st.caption("yfinance + Plotly 기반 수익률 / 차트 비교 도구")

# ----------------------------
# 주요 종목 사전 정의
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
# 사이드바 - 사용자 입력
# ----------------------------
st.sidebar.header("⚙️ 분석 설정")

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요 (여러 개 가능)",
    options=list(STOCK_DICT.keys()),
    default=["🇰🇷 삼성전자", "🇺🇸 애플(Apple)", "🇺🇸 엔비디아(NVIDIA)"]
)

period_option = st.sidebar.selectbox(
    "분석 기간을 선택하세요",
    options=["1개월", "3개월", "6개월", "1년", "3년", "5년"],
    index=3
)

period_map = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "3년": "3y",
    "5년": "5y",
}

# ----------------------------
# 데이터 불러오기 함수 (캐시 사용)
# ----------------------------
@st.cache_data(ttl=3600)
def load_stock_data(ticker, period):
    """yfinance로 주가 데이터를 불러온다."""
    try:
        df = yf.download(
            ticker,
            period=period,
            progress=False,
            auto_adjust=True
        )
        # 멀티인덱스 컬럼 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"{ticker} 데이터를 불러오는 중 오류: {e}")
        return pd.DataFrame()


# ----------------------------
# 메인 로직
# ----------------------------
if not selected_names:
    st.warning("👈 사이드바에서 비교할 종목을 1개 이상 선택해주세요.")
    st.stop()

period_code = period_map[period_option]

price_data = {}
return_data = {}

with st.spinner("주가 데이터를 불러오는 중입니다..."):
    for name in selected_names:
        ticker = STOCK_DICT[name]
        df = load_stock_data(ticker, period_code)

        if df.empty or "Close" not in df.columns:
            st.warning(f"⚠️ '{name}' 데이터를 불러올 수 없습니다.")
            continue

        df = df.dropna(subset=["Close"])
        if len(df) < 2:
            st.warning(f"⚠️ '{name}' 데이터가 충분하지 않습니다.")
            continue

        price_data[name] = df["Close"]
        start_price = df["Close"].iloc[0]
        return_data[name] = (df["Close"] / start_price - 1) * 100

if not price_data:
    st.error("표시할 데이터가 없습니다. 다른 종목이나 기간을 선택해주세요.")
    st.stop()

# ----------------------------
# 1. 수익률 요약 테이블
# ----------------------------
st.subheader("📊 기간 수익률 요약")

summary_rows = []
for name, returns in return_data.items():
    final_return = float(returns.iloc[-1])
    start_price = float(price_data[name].iloc[0])
    end_price = float(price_data[name].iloc[-1])
    summary_rows.append({
        "종목": name,
        "시작가": round(start_price, 2),
        "현재가": round(end_price, 2),
        "수익률(%)": round(final_return, 2)
    })

summary_df = pd.DataFrame(summary_rows)


# 수익률 색상 강조 함수
def highlight_return(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    color = "red" if v > 0 else ("blue" if v < 0 else "black")
    return f"color: {color}; font-weight: bold;"


# pandas 버전에 따라 map / applymap 안전하게 적용
styled_df = summary_df.style
if hasattr(styled_df, "map"):
    # pandas 2.1.0 이상
    styled_df = styled_df.map(highlight_return, subset=["수익률(%)"])
else:
    # 구버전 pandas
    styled_df = styled_df.applymap(highlight_return, subset=["수익률(%)"])

# 숫자 포맷 적용
styled_df = styled_df.format({
    "시작가": "{:,.2f}",
    "현재가": "{:,.2f}",
    "수익률(%)": "{:+.2f}"
})

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

# ----------------------------
# 2. 누적 수익률 비교 차트
# ----------------------------
st.subheader("📈 누적 수익률 비교 (%)")
st.caption("선택 기간 시작일을 0%로 두고 비교합니다.")

fig_return = go.Figure()
for name, returns in return_data.items():
    fig_return.add_trace(
        go.Scatter(
            x=returns.index,
            y=returns.values,
            mode="lines",
            name=name,
            hovertemplate="%{x|%Y-%m-%d}<br>수익률: %{y:.2f}%<extra></extra>"
        )
    )

fig_return.update_layout(
    xaxis_title="날짜",
    yaxis_title="누적 수익률 (%)",
    hovermode="x unified",
    template="plotly_white",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
)
fig_return.add_hline(y=0, line_dash="dash", line_color="gray")

st.plotly_chart(fig_return, use_container_width=True)

# ----------------------------
# 3. 개별 종목 주가 차트
# ----------------------------
st.subheader("💹 개별 종목 주가 차트")

selected_for_detail = st.selectbox(
    "상세 차트를 볼 종목을 선택하세요",
    options=list(price_data.keys())
)

if selected_for_detail:
    ticker = STOCK_DICT[selected_for_detail]
    df_detail = load_stock_data(ticker, period_code)
    df_detail = df_detail.dropna(subset=["Close"])

    has_ohlc = all(col in df_detail.columns for col in ["Open", "High", "Low", "Close"])

    if has_ohlc and len(df_detail) > 1:
        fig_price = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{selected_for_detail} 주가", "거래량")
        )

        fig_price.add_trace(
            go.Candlestick(
                x=df_detail.index,
                open=df_detail["Open"],
                high=df_detail["High"],
                low=df_detail["Low"],
                close=df_detail["Close"],
                name="주가",
                increasing_line_color="red",
                decreasing_line_color="blue"
            ),
            row=1, col=1
        )

        if "Volume" in df_detail.columns:
            fig_price.add_trace(
                go.Bar(
                    x=df_detail.index,
                    y=df_detail["Volume"],
                    name="거래량",
                    marker_color="lightgray"
                ),
                row=2, col=1
            )

        fig_price.update_layout(
            template="plotly_white",
            height=600,
            xaxis_rangeslider_visible=False,
            showlegend=False
        )

        st.plotly_chart(fig_price, use_container_width=True)
    else:
        fig_line = go.Figure()
        fig_line.add_trace(
            go.Scatter(
                x=df_detail.index,
                y=df_detail["Close"],
                mode="lines",
                name="종가"
            )
        )
        fig_line.update_layout(
            template="plotly_white",
            height=500,
            yaxis_title="종가"
        )
        st.plotly_chart(fig_line, use_container_width=True)

# ----------------------------
# 푸터
# ----------------------------
st.divider()
st.caption("📌 데이터 출처: Yahoo Finance (yfinance) | 본 자료는 학습용이며 투자 권유가 아닙니다.")

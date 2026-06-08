import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="종목 분석 순위", page_icon="🏆", layout="wide")

st.title("🏆 종목 분석 순위 (정량 지표)")
st.caption("수익률·변동성·위험대비수익을 비교합니다. (투자 권유 아님)")

# ----------------------------
# 종목 사전 (대폭 확대)
# ----------------------------
STOCK_DICT = {
    # 🇰🇷 한국 주요 종목
    "🇰🇷 삼성전자": "005930.KS",
    "🇰🇷 SK하이닉스": "000660.KS",
    "🇰🇷 LG에너지솔루션": "373220.KS",
    "🇰🇷 삼성바이오로직스": "207940.KS",
    "🇰🇷 현대차": "005380.KS",
    "🇰🇷 기아": "000270.KS",
    "🇰🇷 NAVER": "035420.KS",
    "🇰🇷 카카오": "035720.KS",
    "🇰🇷 LG화학": "051910.KS",
    "🇰🇷 POSCO홀딩스": "005490.KS",
    "🇰🇷 삼성SDI": "006400.KS",
    "🇰🇷 현대모비스": "012330.KS",
    "🇰🇷 KB금융": "105560.KS",
    "🇰🇷 신한지주": "055550.KS",
    "🇰🇷 셀트리온": "068270.KS",
    # 🇺🇸 미국 주요 종목
    "🇺🇸 애플(Apple)": "AAPL",
    "🇺🇸 마이크로소프트(Microsoft)": "MSFT",
    "🇺🇸 엔비디아(NVIDIA)": "NVDA",
    "🇺🇸 테슬라(Tesla)": "TSLA",
    "🇺🇸 아마존(Amazon)": "AMZN",
    "🇺🇸 구글(Alphabet)": "GOOGL",
    "🇺🇸 메타(Meta)": "META",
    "🇺🇸 넷플릭스(Netflix)": "NFLX",
    "🇺🇸 AMD": "AMD",
    "🇺🇸 인텔(Intel)": "INTC",
    "🇺🇸 코카콜라(Coca-Cola)": "KO",
    "🇺🇸 맥도날드(McDonald's)": "MCD",
    "🇺🇸 디즈니(Disney)": "DIS",
    "🇺🇸 비자(Visa)": "V",
    "🇺🇸 JP모건(JPMorgan)": "JPM",
}

# ----------------------------
# 사이드바 입력
# ----------------------------
st.sidebar.header("⚙️ 분석 설정")

# 전체 선택 옵션
select_all = st.sidebar.checkbox("📋 목록의 모든 종목 선택", value=False)

if select_all:
    default_selection = list(STOCK_DICT.keys())
else:
    default_selection = ["🇰🇷 삼성전자", "🇺🇸 애플(Apple)", "🇺🇸 엔비디아(NVIDIA)"]

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요",
    options=list(STOCK_DICT.keys()),
    default=default_selection
)

# 티커 직접 입력 (목록에 없는 종목)
st.sidebar.markdown("---")
custom_input = st.sidebar.text_input(
    "✍️ 직접 티커 입력 (쉼표로 구분)",
    placeholder="예: 005930.KS, AAPL, TSLA"
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
# 분석 대상 티커 정리
# ----------------------------
# 선택한 종목 → {이름: 티커}
target = {name: STOCK_DICT[name] for name in selected_names}

# 직접 입력한 티커 추가
if custom_input.strip():
    for t in custom_input.split(","):
        t = t.strip().upper()
        if t:
            target[t] = t   # 이름과 티커를 동일하게 사용

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
    except Exception:
        return pd.DataFrame()

# ----------------------------
# 데이터 준비
# ----------------------------
if not target:
    st.warning("👈 사이드바에서 종목을 선택하거나 티커를 입력해주세요.")
    st.stop()

# 너무 많으면 경고
if len(target) > 30:
    st.warning(f"⚠️ 선택한 종목이 {len(target)}개입니다. 많을수록 로딩이 느려질 수 있어요.")

period_code = period_map[period_option]

price_data = {}
return_data = {}
failed = []

progress = st.progress(0, text="데이터를 불러오는 중...")
items = list(target.items())

for i, (name, ticker) in enumerate(items):
    df = load_stock_data(ticker, period_code)

    if df.empty or "Close" not in df.columns:
        failed.append(name)
    else:
        df = df.dropna(subset=["Close"])
        if len(df) < 2:
            failed.append(name)
        else:
            price_data[name] = df["Close"]
            start_price = df["Close"].iloc[0]
            return_data[name] = (df["Close"] / start_price - 1) * 100

    progress.progress((i + 1) / len(items), text=f"{name} 처리 중... ({i+1}/{len(items)})")

progress.empty()

if failed:
    st.info(f"ℹ️ 불러오지 못한 종목: {', '.join(failed)}")

if not price_data:
    st.error("표시할 데이터가 없습니다. 종목/기간을 확인해주세요.")
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
# 표시
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

# 해설
best = analysis_df.iloc[0]
st.info(
    f"📌 **'{best['종목']}'** 이(가) 선택 기간 동안 "
    f"**위험 대비 수익**이 가장 높았습니다. "
    f"(수익률 {best['수익률(%)']:+.2f}%, 변동성 {best['변동성(%)']:.2f}%)\n\n"
    f"⚠️ 과거 데이터일 뿐 미래 수익을 보장하지 않습니다."
)

st.divider()
st.caption("📌 데이터 출처: Yahoo Finance | 학습용 자료이며 투자 권유가 아닙니다.")

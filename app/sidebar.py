import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()

def init_session_state():
    """初始化所有全局 Session State 變數"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "BTC"
    if "show_dashboard" not in st.session_state:
        st.session_state.show_dashboard = False
    if "trading_persona" not in st.session_state:
        st.session_state.trading_persona = "Conservative"
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "order_history" not in st.session_state:
        st.session_state.order_history = []
    if "portfolio_balance" not in st.session_state:
        st.session_state.portfolio_balance = 10000.0  # 初始模擬資金
    if "positions" not in st.session_state:
        st.session_state.positions = {}  # {symbol: {amount, avg_price}}

def render_sidebar():
    """渲染側邊欄並返回分析工具與模型設定"""
    with st.sidebar:
        # === 1. Switch Button -> 地端模型 / 雲端模型 ===
        gemini_key = os.getenv("GEMINI_API_KEY", "")

        # === 2. 情緒 Block ===
        st.subheader("👥 社群情緒")
        enable_fear_greed = st.checkbox("恐懼貪婪指數", value=True)
        enable_long_short = st.checkbox("多空投票比", value=True)
        enable_news = st.checkbox("新聞", value=True)
        st.divider()

        # === 3. 技術指標 Block ===
        st.subheader("📈 技術指標工具")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            enable_bb = st.checkbox("布林通道", value=True)
            enable_rsi = st.checkbox("RSI", value=True)
        with col_t2:
            enable_ma = st.checkbox("MA", value=True)
            enable_ema = st.checkbox("EMA", value=True)

        st.divider()

        # === 4. 出入場判斷 Block ===
        st.subheader("🎯 出入場策略")
        enable_bb_1h = st.checkbox("布林 1hr 策略", value=True)
        enable_bb_6h = st.checkbox("布林 6hr 策略", value=True)

        st.divider()

    # 回傳結構化的設定字典
    return {
        "gemini_api_key": gemini_key,
        "sentiment_tools": {
            "fear_greed": enable_fear_greed,
            "long_short": enable_long_short,
            "news": enable_news,
        },
        "tech_tools": {
            "bollinger": enable_bb,
            "rsi": enable_rsi,
            "ma": enable_ma,
            "ema": enable_ema,
        },
        "strategy_tools": {
            "bollinger_1h": enable_bb_1h,
            "bollinger_6h": enable_bb_6h,
        }
    }
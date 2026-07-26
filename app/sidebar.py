import streamlit as st

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
    """渲染側邊欄並返回分析工具設定"""
    with st.sidebar:
        st.title("分析工具開關")
        enable_bollinger = st.checkbox("布林通道 (Bollinger Bands)", value=True)
        enable_ma = st.checkbox("移動平均線 (Moving Averages)", value=True)
        enable_sentiment = st.checkbox("社群情緒分析 (Social Sentiment)", value=True)
        
        st.divider()
        
    return {
        "bollinger": enable_bollinger,
        "ma": enable_ma,
        "sentiment": enable_sentiment
    }
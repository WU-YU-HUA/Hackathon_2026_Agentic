"""
加密貨幣 AI Agent 交易助手 - Streamlit 版本
"""
import streamlit as st
from app.sidebar import init_session_state, render_sidebar
from app.chat_tab import render_chat_tab
from app.order_tab import render_order_tab

# ===== 頁面全局配置 =====
st.set_page_config(
    page_title="加密貨幣 AI 交易助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. 初始化 Session State
init_session_state()

# 2. 渲染側邊欄並獲取設定數據
tools_config = render_sidebar()

# 3. 主頁面標題
st.title("🤖 加密貨幣 AI Agent 交易助手")

# 4. 多頁籤架構
tab1, tab2 = st.tabs(["💬 AI Agent 對話與分析", "📈 模擬下單"])

with tab1:
    render_chat_tab(tools_config)

with tab2:
    render_order_tab()

# ===== 頁尾 =====
st.divider()
st.caption("⚠️ 風險提示：本系統僅供學習與模擬使用，實際交易請謹慎評估風險。")
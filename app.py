"""
加密貨幣 AI Agent 交易助手 - Streamlit 主程式入口
"""
import streamlit as st
from app.sidebar import init_session_state, render_sidebar
from app.chat_tab import render_chat_tab
from app.order_tab import render_order_tab

# ===== 1. 頁面全局配置 =====
st.set_page_config(
    page_title="加密貨幣 AI 交易助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== 2. 視覺微優化 (移除頂部多餘留白) =====
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# ===== 3. 初始化全局 Session State =====
init_session_state()

# ===== 4. 渲染側邊欄並獲取設定數據 (包含模型選擇與工具清單) =====
tools_config = render_sidebar()

# ===== 5. 主頁面標題 =====
st.title("🤖 加密貨幣 AI Agent 交易助手")

# ===== 6. 多頁籤架構 =====
# 將「模擬下單」改為「MAX 實盤交易」，強調真實 API 串接能力
tab1, tab2 = st.tabs(["💬 AI Agent 對話與分析", "📈 MAX 實盤交易"])

with tab1:
    render_chat_tab(tools_config)

with tab2:
    render_order_tab()

# ===== 7. 頁尾警告標語 =====
st.divider()

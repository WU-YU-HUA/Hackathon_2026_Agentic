"""
加密貨幣 AI Agent 交易助手 - Streamlit 主程式入口
"""
import streamlit as st
from app.sidebar import init_session_state, render_sidebar
from app.chat_tab import render_chat_tab          # 原本的表單+儀表板報告
from app.agent_tab import render_agent_tab        # 🌟 新增：自由對話 Agent
from app.order_tab import render_order_tab        # MAX 實盤下單

st.set_page_config(page_title="加密貨幣 AI 交易助手", page_icon="🤖", layout="wide")

# 視覺微優化
st.markdown("""<style>.block-container { padding-top: 1.8rem; padding-bottom: 1rem; }</style>""", unsafe_allow_html=True)

init_session_state()
tools_config = render_sidebar()

st.title("🤖 加密貨幣 AI Agent 交易助手")

# 🌟 分成三個核心功能區塊
tab1, tab2, tab3 = st.tabs([
    "📰 結構化報告", 
    "💬 Crypto Chatbot", 
    "📈 MAX 實盤交易"
])

with tab1:
    render_chat_tab(tools_config) # 你原本那套點擊按鈕、顯示圖表的邏輯

with tab2:
    render_agent_tab(tools_config) # 🌟 新增的純聊天介面

with tab3:
    render_order_tab()

st.divider()
st.caption("⚠️ 風險提示：本系統僅供學習與策略分析使用，實際交易請謹慎評估風險。")
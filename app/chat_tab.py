# app/chat_tab.py
import streamlit as st
from app.components.onboarding import render_risk_selector, render_pair_selector
from app.components.dashboard import render_dashboard
from api.getData import CryptoData
from api.fearGreed import FearGreedData
from api.social import coinGeckoVote
from api.symbol_mapping import get_coingecko_id

def render_chat_tab(tools_config):
    st.header("🤖 AI 投資助手")

    # Session State 初始化
    if 'risk_level' not in st.session_state: st.session_state.risk_level = None
    if 'selected_pair' not in st.session_state: st.session_state.selected_pair = None
    if 'show_dashboard' not in st.session_state: st.session_state.show_dashboard = False

    # 步驟 1: 選擇風險
    if st.session_state.risk_level is None:
        render_risk_selector()
        return

    # 步驟 2: 選擇交易對
    if st.session_state.selected_pair is None:
        render_pair_selector()
        return

    # 步驟 3: 對話與報告區域
    st.write(f"**風險等級**: {st.session_state.risk_level} | **交易對**: {st.session_state.selected_pair}")
    if st.button("🔄 重新開始"):
        st.session_state.risk_level = None
        st.session_state.selected_pair = None
        st.session_state.show_dashboard = False
        st.rerun()

    # 顯示對話紀錄
    for chat in st.session_state.chat_history:
        st.chat_message(chat["role"]).write(chat["content"])

    # 數據獲取 (可於此處替換為 AI Agent 觸發)
    if not st.session_state.show_dashboard and st.session_state.selected_pair:
        with st.spinner('正在獲取分析數據...'):
            symbol = st.session_state.current_symbol
            pair = st.session_state.selected_pair
            
            st.session_state.analysis_result = {
                "symbol": symbol, "pair": pair, "risk_level": st.session_state.risk_level,
                "tech_data": CryptoData().get_technical_data(symbol=pair.lower(), interval="1h", period=100),
                "fear_greed": FearGreedData(limit=1).get_raw_data(),
                "social": coinGeckoVote(get_coingecko_id(symbol))
            }
            st.session_state.show_dashboard = True
            st.rerun()

    # 渲染視覺化儀表板
    if st.session_state.show_dashboard and st.session_state.analysis_result:
        render_dashboard(st.session_state.analysis_result)

    # 輸入對話框
    if user_input := st.chat_input("繼續對話或詢問其他問題..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        # 此處後續直接對接 LLM Agent 的 Function Calling 邏輯
        st.rerun()
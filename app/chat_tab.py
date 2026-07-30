# app/chat_tab.py
import streamlit as st
import json  # 👈 記得新增引入 json
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
    
    # 記錄初始的側邊欄設定
    if 'chat_last_config' not in st.session_state: 
        st.session_state.chat_last_config = json.dumps(tools_config, sort_keys=True)

    # ==========================================
    # 🌟 新增：偵測側邊欄設定變更 (Smart Config Tracker)
    # ==========================================
    current_config_str = json.dumps(tools_config, sort_keys=True)
    if st.session_state.chat_last_config != current_config_str:
        # 更新記憶
        st.session_state.chat_last_config = current_config_str
        
        # 如果已經完成前兩題問答 (儀表板正在顯示)，則強制重新獲取資料
        if st.session_state.show_dashboard:
            st.session_state.show_dashboard = False
            st.toast("🔧 偵測到設定變更，正在為您重新獲取最新數據！", icon="✨")
            st.rerun()

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

    # ==========================================
    # 🌟 數據獲取 (根據 sidebar 設定動態呼叫 API)
    # ==========================================
    if not st.session_state.show_dashboard and st.session_state.selected_pair:
        with st.spinner('正在獲取分析數據...'):
            symbol = st.session_state.current_symbol
            pair = st.session_state.selected_pair
            
            # 解析側邊欄的勾選狀態
            sentiment_config = tools_config.get("sentiment_tools", {})
            tech_config = tools_config.get("tech_tools", {})
            
            # 準備基礎資料包
            result_data = {
                "symbol": symbol, 
                "pair": pair, 
                "risk_level": st.session_state.risk_level,
                "tech_data": None,
                "fear_greed": None,
                "social": None,
                "tools_config": tools_config  # 👈 把最新設定檔傳給 dashboard
            }
            
            # 1. 判斷是否需要抓取技術指標 (只要有勾任何一個就抓)
            if any(tech_config.values()):
                result_data["tech_data"] = CryptoData().get_technical_data(symbol=pair.lower(), interval="1h", period=100)
                
            # 2. 判斷是否需要抓取恐懼貪婪指數
            if sentiment_config.get("fear_greed"):
                result_data["fear_greed"] = FearGreedData(limit=1).get_raw_data()
                
            # 3. 判斷是否需要抓取多空投票比
            if sentiment_config.get("long_short"):
                result_data["social"] = coinGeckoVote(get_coingecko_id(symbol))
            
            # 儲存結果並準備渲染
            st.session_state.analysis_result = result_data
            st.session_state.show_dashboard = True
            st.rerun()

    # ==========================================
    # 渲染視覺化儀表板
    # ==========================================
    if st.session_state.show_dashboard and st.session_state.analysis_result:
        # 將包含 tools_config 的資料包傳給 render_dashboard
        render_dashboard(st.session_state.analysis_result)
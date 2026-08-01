# app/chat_tab.py
import streamlit as st
import json
from app.components.onboarding import render_risk_selector, render_pair_selector
from app.components.dashboard import render_dashboard
from api.getData import fetch_technical_data  # 🌟 更新匯入
from api.social import get_vote_feargreed       # 🌟 更新匯入
from app.components.report_generator import generate_html_report, generate_ai_report_markdown

def render_chat_tab(tools_config):
    st.header("🤖 AI 投資助手")

    # Session State 初始化
    if 'risk_level' not in st.session_state: st.session_state.risk_level = None
    if 'selected_pair' not in st.session_state: st.session_state.selected_pair = None
    if 'show_dashboard' not in st.session_state: st.session_state.show_dashboard = False
    if 'chat_history' not in st.session_state: st.session_state.chat_history = []
    
    # 記錄初始的側邊欄設定
    if 'chat_last_config' not in st.session_state: 
        st.session_state.chat_last_config = json.dumps(tools_config, sort_keys=True)

    # 偵測側邊欄設定變更 (Smart Config Tracker)
    current_config_str = json.dumps(tools_config, sort_keys=True)
    if st.session_state.chat_last_config != current_config_str:
        st.session_state.chat_last_config = current_config_str
        
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
        if 'ai_report_md' in st.session_state:
            del st.session_state.ai_report_md
        st.rerun()

    # 顯示對話紀錄
    for chat in st.session_state.chat_history:
        st.chat_message(chat["role"]).write(chat["content"])

    # ==========================================
    # 🌟 數據獲取 (使用最新整合的 Lambda 模組)
    # ==========================================
    if not st.session_state.show_dashboard and st.session_state.selected_pair:
        with st.spinner('正在獲取分析數據...'):
            symbol = st.session_state.get("current_symbol", "BTC")
            pair = st.session_state.selected_pair
            
            # 格式化交易對名稱
            symbol_param = pair.upper() if pair.upper().endswith("USDT") else f"{pair.upper()}USDT"

            sentiment_config = tools_config.get("sentiment_tools", {})
            tech_config = tools_config.get("tech_tools", {})
            
            # 建立整合資料包
            result_data = {
                "symbol": symbol, 
                "pair": pair, 
                "risk_level": st.session_state.risk_level,
                "kline_response": {},
                "social_fg_data": {},
                "tools_config": tools_config
            }
            
            # 1. 抓取技術指標 (一次拿到 15m, 1h, 6h, 1d 數據)
            if any(tech_config.values()):
                kline_res = fetch_technical_data("ChatTab Tech Fetch", {"symbol": symbol_param})
                result_data["kline_response"] = kline_res

            # 2. 抓取社群情緒與恐懼貪婪指數 (合併呼叫)
            if sentiment_config.get("fear_greed") or sentiment_config.get("long_short"):
                social_fg_res = get_vote_feargreed("ChatTab Social Fetch", {"symbol": symbol.lower(), "limit": 1})
                result_data["social_fg_data"] = social_fg_res
                result_data["fear_greed"] = social_fg_res.get("fear_greed")
                result_data["social"] = social_fg_res.get("social")
            
            # 儲存結果並準備渲染
            st.session_state.analysis_result = result_data
            st.session_state.show_dashboard = True
            st.rerun()

    # ==========================================
    # 🌟 渲染 Dashboard 與 AI 報告
    # ==========================================
    if st.session_state.show_dashboard and st.session_state.get("analysis_result"):
        render_dashboard(st.session_state.analysis_result)
        
        st.divider()
        
        col_title, col_btn = st.columns([3, 1])
        with col_title:
            st.subheader("📝 AI 綜合分析與投資建議")
            
        if 'ai_report_md' not in st.session_state:
            with st.spinner("🤖 AI 正在根據您的風險等級撰寫專屬報告..."):
                api_key = tools_config.get("gemini_api_key")
                st.session_state.ai_report_md = generate_ai_report_markdown(st.session_state.analysis_result, api_key)
        
        st.markdown(st.session_state.ai_report_md)
        
        with col_btn:
            html_string = generate_html_report(st.session_state.analysis_result, st.session_state.ai_report_md)
            
            st.download_button(
                label="📥 下載 HTML 報告",
                data=html_string.encode('utf-8'),
                file_name=f"{st.session_state.analysis_result.get('symbol')}_投資報告.html",
                mime="text/html",
                use_container_width=True,
                type="primary"
            )
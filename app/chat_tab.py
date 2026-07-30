# app/chat_tab.py
import streamlit as st
import json  # 👈 記得新增引入 json
from app.components.onboarding import render_risk_selector, render_pair_selector
from app.components.dashboard import render_dashboard
from api.getData import CryptoData
from api.fearGreed import FearGreedData
from api.social import coinGeckoVote
from api.symbol_mapping import get_coingecko_id
from app.components.report_generator import generate_html_report, generate_ai_report_markdown

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
                # 儀表板顯示用的主數據 (預設 1h)
                primary_tech = CryptoData().get_technical_data(symbol=pair.lower(), interval="1h", period=100)
                result_data["tech_data"] = primary_tech
                
                # 🌟 修改為 1h, 6h, 1d (提供給 AI 寫報告)
                result_data["multi_timeframe"] = {
                    "短期_1h": primary_tech,
                    "中期_6h": CryptoData().get_technical_data(symbol=pair.lower(), interval="6h", period=100),
                    "長期_1d": CryptoData().get_technical_data(symbol=pair.lower(), interval="1d", period=100)
                }
                
                # 🚧 預留空間：未來把你寫好的布林通道策略結果塞在這裡
                # result_data["custom_bb_strategy"] = your_custom_bb_function(pair)
                result_data["custom_bb_strategy"] = None

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

# (在 render_dashboard 下方新增...)

    if st.session_state.show_dashboard and st.session_state.analysis_result:
        # 1. 渲染你寫好的圖表
        render_dashboard(st.session_state.analysis_result)
        
        st.divider()
        
        # 2. 準備排版
        col_title, col_btn = st.columns([3, 1])
        with col_title:
            st.subheader("📝 AI 綜合分析與投資建議")
            
        # 3. 呼叫我們封裝好的模組來生報告
        if 'ai_report_md' not in st.session_state:
            with st.spinner("🤖 AI 正在根據您的風險等級撰寫專屬報告..."):
                api_key = tools_config.get("gemini_api_key")
                # ✨ 超級乾淨，只有一行！
                st.session_state.ai_report_md = generate_ai_report_markdown(st.session_state.analysis_result, api_key)
        
        # 4. 在畫面上顯示 AI 寫好的報告
        st.markdown(st.session_state.ai_report_md)
        
        # 5. 生成 HTML 字串並放置下載按鈕
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
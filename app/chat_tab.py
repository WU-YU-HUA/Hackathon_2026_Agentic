# app/chat_tab.py
import streamlit as st
import json
from app.components.onboarding import render_risk_selector, render_pair_selector
from app.components.dashboard import render_dashboard
from api.getData import fetch_technical_data 
from api.social import get_vote_feargreed       
from api.news import fetch_news
from api.news_ai import invoke_analyzer
from api.kline_ai import invoke_kline_analyzer
from api.social_ai import invoke_social_analyzer
from app.components.report_generator import generate_html_report
from api.ai_report import invoke_summary_analyzer  

def filter_kline_data(kline_data, tech_config):
    """根據使用者的側邊欄設定，過濾掉未勾選的指標欄位，讓 Payload 更乾淨"""
    if not kline_data:
        return {}

    # 永遠保留的基礎 K 線欄位
    allowed_keys = {"timestamp", "open", "high", "low", "close", "volume"}
    
    # 根據勾選狀態，動態加入允許的欄位
    if tech_config.get("bollinger"):
        allowed_keys.update(["bb_middle", "bb_upper", "bb_lower"])
    if tech_config.get("rsi"):
        allowed_keys.add("rsi")
    if tech_config.get("ma"):
        allowed_keys.update(["ma_7", "ma_25", "ma_99"])
    if tech_config.get("ema"):
        allowed_keys.update(["ema_7", "ema_25", "ema_99"])

    clean_data = {}
    for interval, records in kline_data.items():
        if isinstance(records, list):
            clean_records = []
            for row in records:
                # 字典推導式：只保留在 allowed_keys 白名單裡的欄位
                clean_row = {k: v for k, v in row.items() if k in allowed_keys}
                clean_records.append(clean_row)
            clean_data[interval] = clean_records
            
    return clean_data

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
        if 'ai_report_data' in st.session_state:
            del st.session_state.ai_report_data
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
            news_config = tools_config.get("news_tools", {})
            # 建立整合資料包
            result_data = {
                "symbol": symbol, 
                "pair": pair, 
                "risk_level": st.session_state.risk_level,
                "kline_response": {},
                "social_fg_data": {},
                "news_report": {},
                "kline_report": {},
                "social_report": {},
                "tools_config": tools_config
            }
            
            # 1. 抓取技術指標 (一次拿到 15m, 1h, 6h, 1d 數據)
            if any(tech_config.values()):
                kline_res = fetch_technical_data("ChatTab Tech Fetch", {"symbol": symbol_param})
                
                # 🌟 核心過濾：將原始資料丟進白名單過濾器
                raw_data = kline_res.get("data", {})
                clean_kline_data = filter_kline_data(raw_data, tech_config)
                
                # 把過濾後乾淨的資料塞回去
                if "data" in kline_res:
                    kline_res["data"] = clean_kline_data

                result_data["kline_response"] = kline_res
                
                # 🌟 將「乾淨無雜質」的資料傳給 kline_analyzer
                result_data["kline_report"] = invoke_kline_analyzer(
                    symbol=symbol_param, 
                    kline_data=clean_kline_data
                )

            # 2. 抓取社群情緒與恐懼貪婪指數 (合併呼叫)
            if sentiment_config.get("fear_greed") or sentiment_config.get("long_short"):
                social_fg_res = get_vote_feargreed("ChatTab Social Fetch", {"symbol": symbol.lower(), "limit": 7})
                result_data["social_fg_data"] = social_fg_res
                result_data["fear_greed"] = social_fg_res.get("fear_and_greed")[0]
                result_data["long_short"] = social_fg_res.get("community_sentiment")
                
                result_data["social_report"] = invoke_social_analyzer(
                    symbol=symbol,
                    fear_and_greed=social_fg_res.get("fear_and_greed"),
                    community_sentiment=social_fg_res.get("community_sentiment")
                )

            if news_config.get("news"):
                news_data = fetch_news(symbol.lower())
                result_data["news_report"] = invoke_analyzer(news_data, symbol.lower())

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
            
        if 'ai_report_data' not in st.session_state:
            with st.spinner("🤖 AI 正在整合各維度數據撰寫專屬報告..."):
                analysis = st.session_state.analysis_result
                
                # 🌟 根據 tools_config 嚴格過濾傳遞給 AI 的報告，沒開啟的直接丟棄為 {}
                cfg_tech = tools_config.get("tech_tools", {})
                cfg_sent = tools_config.get("sentiment_tools", {})
                cfg_news = tools_config.get("news_tools", {})
                
                # 若有任何技術指標開啟，才傳遞 kline_report
                clean_tech_report = analysis.get("kline_report", {}) if any(cfg_tech.values()) else {}
                
                # 若有任何情緒指標開啟，才傳遞 social_report
                clean_social_report = analysis.get("social_report", {}) if (cfg_sent.get("fear_greed") or cfg_sent.get("long_short")) else {}
                
                # 若新聞開啟，才傳遞 news_report
                clean_news_report = analysis.get("news_report", {}) if cfg_news.get("news") else {}
                
                try:
                    st.session_state.ai_report_data = invoke_summary_analyzer(
                        symbol=analysis.get("symbol", "BTC"),
                        risk_level=analysis.get("risk_level", 5),
                        technical_report=clean_tech_report,
                        social_report=clean_social_report,
                        news_report=clean_news_report
                    )
                except Exception as e:
                    st.error(f"⚠️ 彙整報告生成失敗: {e}")
                    st.session_state.ai_report_data = {}
        
        # 提取 Markdown 報告並渲染
        report_md = st.session_state.ai_report_data.get("report_markdown", "⚠️ 無法取得 AI 報告內容。")
        st.markdown(report_md)
        
        with col_btn:
            # 傳遞完整的 JSON 給 HTML 產生器
            html_string = generate_html_report(st.session_state.analysis_result, st.session_state.ai_report_data)
            
            st.download_button(
                label="📥 下載 HTML 報告",
                data=html_string.encode('utf-8'),
                file_name=f"{st.session_state.analysis_result.get('symbol')}_投資報告.html",
                mime="text/html",
                use_container_width=True,
                type="primary"
            )
# app/components/dashboard.py
import streamlit as st
import pandas as pd
from app.components.charts import create_gauge_chart, create_candlestick_chart
from api.getData import fetch_technical_data
from api.social import get_vote_feargreed

def get_last_record(data_list):
    """安全取得清單中的最後一筆數據 (最新 K 棒數據)"""
    if isinstance(data_list, list) and len(data_list) > 0:
        return data_list[-1]
    elif isinstance(data_list, dict):
        return data_list
    return {}

def _render_report_content(report_data):
    """內部輔助函式：安全渲染 AI 報告內容 (支援 dict 與 str)"""
    if not report_data:
        return
    if isinstance(report_data, str):
        st.markdown(report_data)
    elif isinstance(report_data, dict):
        # 優先渲染 report / content 欄位，若沒有則轉字串
        content = report_data.get("report") or report_data.get("content") or str(report_data)
        st.markdown(content)

def render_dashboard(analysis_result):
    """渲染儀表板整體數據卡片與圖表 (支援動態開關設定與指定排序)"""
    st.divider()
    
    # === 0. 讀取數據與設定檔 ===
    tools_config = analysis_result.get("tools_config", {})
    sentiment_config = tools_config.get("sentiment_tools", {})
    tech_config = tools_config.get("tech_tools", {})
    news_config = tools_config.get("news_tools", {})
    
    # 取出 K 線 Response (優先使用已載入的，沒有才呼叫)
    kline_response = analysis_result.get("kline_response", {})
    if not kline_response and any(tech_config.values()):
        base_symbol = analysis_result.get('symbol', 'BTC').upper()
        symbol_param = base_symbol if base_symbol.endswith("USDT") else f"{base_symbol}USDT"
        kline_response = fetch_technical_data("Dashboard K-Line Fetch", {"symbol": symbol_param})
    
    kline_data = kline_response.get('data', {}) if isinstance(kline_response, dict) else {}
    
    # 取得各週期 K 線 Data 的最後一筆資料 (即時數據)
    last_15m = get_last_record(kline_data.get("15m_data", []))
    last_1h  = get_last_record(kline_data.get("1h_data", []))
    last_6h  = get_last_record(kline_data.get("6h_data", []))
    last_1d  = get_last_record(kline_data.get("1d_data", []))

    # 預設採用 1h 的最後一筆作為主要參考指標
    main_last = last_1h if last_1h else (last_15m or last_1d or {})

    raw_social_fg = analysis_result.get('social_fg_data', {})
    fear_greed_data = analysis_result.get('fear_greed') or raw_social_fg.get('fear_greed', {})
    social_data = analysis_result.get('long_short') or raw_social_fg.get('long_short', {})

    # ==========================================
    # === 1. News 報告 ===
    # ==========================================
    news_report = analysis_result.get("news_report")
    if news_config.get("news") and news_report:
        st.subheader("📰 新聞分析報告")
        _render_report_content(news_report)
        st.divider()

    # ==========================================
    # === 2. 技術 Chart / 數據表格 ===
    # ==========================================
    if any(tech_config.values()):
        st.subheader("📊 技術指標最新數據 (最後一筆 K 棒)")
        col1, col2 = st.columns(2)
        
        with col1:
            # 2-1. 移動平均線 (MA)
            if tech_config.get("ma"):
                st.markdown("#### 移動平均線 (MA - 1h最新)")
                st.dataframe(pd.DataFrame({
                    '週期': ['MA 7', 'MA 25', 'MA 99'],
                    '數值': [
                        f"${main_last.get('ma_7', main_last.get('ma7', 0)):,.2f}",
                        f"${main_last.get('ma_25', main_last.get('ma25', 0)):,.2f}",
                        f"${main_last.get('ma_99', main_last.get('ma99', 0)):,.2f}"
                    ]
                }), hide_index=True, use_container_width=True)
                
            # 2-2. 指數移動平均線 (EMA)
            if tech_config.get("ema"):
                st.markdown("#### 指數移動平均線 (EMA - 1h最新)")
                st.dataframe(pd.DataFrame({
                    '週期': ['EMA 7', 'EMA 25', 'EMA 99'],
                    '數值': [
                        f"${main_last.get('ema_7', main_last.get('ema7', 0)):,.2f}",
                        f"${main_last.get('ema_25', main_last.get('ema25', 0)):,.2f}",
                        f"${main_last.get('ema_99', main_last.get('ema99', 0)):,.2f}"
                    ]
                }), hide_index=True, use_container_width=True)
                
        with col2:
            # 2-3. 布林通道 (Bollinger Bands)
            if tech_config.get("bollinger"):
                st.markdown("#### 布林通道 (Bollinger Bands - 1h最新)")
                bb_upper = main_last.get('upper', main_last.get('bb_upper', 0))
                bb_middle = main_last.get('middle', main_last.get('bb_middle', 0))
                bb_lower = main_last.get('lower', main_last.get('bb_lower', 0))
                
                st.dataframe(pd.DataFrame({
                    '指標': ['上軌', '中軌', '下軌'],
                    '數值': [
                        f"${bb_upper:,.2f}",
                        f"${bb_middle:,.2f}",
                        f"${bb_lower:,.2f}"
                    ]
                }), hide_index=True, use_container_width=True)

            # 2-4. 各週期最新價格與 RSI 對比表
            st.markdown("#### 跨週期最新數據快照")
            snap_data = {
                '週期': ['15m', '1h', '6h', '1d'],
                '最新收盤價': [
                    f"${last_15m.get('close', last_15m.get('price', 0)):,.2f}",
                    f"${last_1h.get('close', last_1h.get('price', 0)):,.2f}",
                    f"${last_6h.get('close', last_6h.get('price', 0)):,.2f}",
                    f"${last_1d.get('close', last_1d.get('price', 0)):,.2f}"
                ]
            }
            if tech_config.get("rsi"):
                snap_data['RSI'] = [
                    f"{float(last_15m.get('rsi', 0)):.2f}",
                    f"{float(last_1h.get('rsi', 0)):.2f}",
                    f"{float(last_6h.get('rsi', 0)):.2f}",
                    f"{float(last_1d.get('rsi', 0)):.2f}"
                ]

            st.dataframe(pd.DataFrame(snap_data), hide_index=True, use_container_width=True)

        st.divider()

    # ==========================================
    # === 3. K 線圖 (多週期 15m, 1h, 6h, 1d) ===
    # ==========================================
    if any(tech_config.values()):
        st.subheader("📈 多週期互動式 K 線圖")
        tab_15m, tab_1h, tab_6h, tab_1d = st.tabs(["超短期 (15m)", "短期 (1h)", "中期 (6h)", "長期 (1d)"])
        
        try:
            base_symbol = analysis_result.get('symbol', 'BTC').upper()
            risk = analysis_result.get('risk_level', '低')

            # 15m
            with tab_15m:
                df_15m = pd.DataFrame(kline_data.get("15m_data", [])[-100:])
                if not df_15m.empty:
                    st.plotly_chart(create_candlestick_chart(df_15m, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 15m K 線數據")

            # 1h
            with tab_1h:
                df_1h = pd.DataFrame(kline_data.get("1h_data", [])[-100:])
                if not df_1h.empty:
                    st.plotly_chart(create_candlestick_chart(df_1h, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 1h K 線數據")
                    
            # 6h
            with tab_6h:
                df_6h = pd.DataFrame(kline_data.get("6h_data", [])[-100:])
                if not df_6h.empty:
                    st.plotly_chart(create_candlestick_chart(df_6h, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 6h K 線數據")
                    
            # 1d
            with tab_1d:
                df_1d = pd.DataFrame(kline_data.get("1d_data", [])[-100:])
                if not df_1d.empty:
                    st.plotly_chart(create_candlestick_chart(df_1d, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 1d K 線數據")
                    
        except Exception as e:
            st.error(f"❌ 繪製 K 線圖失敗: {str(e)}")

        st.divider()

    # ==========================================
    # === 4. K 線報告 ===
    # ==========================================
    kline_report = analysis_result.get("kline_report")
    if any(tech_config.values()) and kline_report:
        st.subheader("🤖 K 線與技術面分析報告")
        _render_report_content(kline_report)
        st.divider()

    # ==========================================
    # === 5. 半圓圖表 (情緒與 RSI 半圓儀表盤) ===
    # ==========================================
    active_gauges = []
    
    # 恐懼貪婪指數
    if sentiment_config.get("fear_greed") and fear_greed_data:
        fg_val = fear_greed_data.get('value', 50) if isinstance(fear_greed_data, dict) else fear_greed_data
        active_gauges.append((float(fg_val), "恐懼貪婪指數"))
        
    # 社群看多比例
    if sentiment_config.get("long_short") and social_data:
        up_val = social_data.get('up', 50) if isinstance(social_data, dict) else social_data
        active_gauges.append((float(up_val), "社群看多比例"))
        
    # RSI 指標 (來自 1h 最後一筆)
    if tech_config.get("rsi") and main_last.get("rsi") is not None:
        rsi_val = main_last.get('rsi', 50)
        active_gauges.append((float(rsi_val), "RSI 指標 (1h)"))

    if active_gauges:
        st.subheader("📊 市場情緒指標")
        cols = st.columns(len(active_gauges))
        for idx, (val, title) in enumerate(active_gauges):
            with cols[idx]:
                st.plotly_chart(create_gauge_chart(val, title), use_container_width=True)
        st.divider()

    # ==========================================
    # === 6. 社群報告 ===
    # ==========================================
    social_report = analysis_result.get("social_report")
    if (sentiment_config.get("fear_greed") or sentiment_config.get("long_short")) and social_report:
        st.subheader("🗣️ 社群情緒分析報告")
        _render_report_content(social_report)
        st.divider()
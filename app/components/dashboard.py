# app/components/dashboard.py
import streamlit as st
import pandas as pd
from app.components.charts import create_gauge_chart, create_candlestick_chart
from api.getData import fetch_technical_data

def get_last_record(data_list):
    """安全取得清單中的最後一筆數據 (最新 K 棒數據)"""
    if isinstance(data_list, list) and len(data_list) > 0:
        return data_list[-1]
    elif isinstance(data_list, dict):
        return data_list
    return {}

# ==========================================
# 🎨 專屬 AI 報告美化渲染器
# ==========================================

def render_news_report_ui(data):
    """1. 📰 新聞分析報告渲染"""
    if isinstance(data, str):
        st.markdown(data)
        return
    if not isinstance(data, dict):
        return

    # 1-1. 情緒與數據概覽 (Metrics)
    overall = data.get("overall_sentiment", {})
    breakdown = data.get("news_breakdown", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("整體情緒", f"{overall.get('label', '未知')}", f"分數: {overall.get('score', 0)}")
    with col2:
        st.metric("分析新聞數", f"{breakdown.get('total', 0)} 則")
    with col3:
        st.metric("利多 / 利空", f"🟢 {breakdown.get('positive', 0)} / 🔴 {breakdown.get('negative', 0)}")
    with col4:
        st.metric("中立新聞", f"⚪ {breakdown.get('neutral', 0)} 則")

    # 1-2. AI 摘要與短/中期影響
    st.info(f"**摘要：** {data.get('summary', '')}")
    
    m_impact = data.get("market_impact", {})
    ic1, ic2 = st.columns(2)
    with ic1:
        st.markdown(f"**短期趨勢：** `:red[{m_impact.get('short_term', '')}]`")
        st.caption(m_impact.get("short_term_reasoning", ""))
    with ic2:
        st.markdown(f"**中期趨勢：** `:orange[{m_impact.get('medium_term', '')}]`")
        st.caption(m_impact.get("medium_term_reasoning", ""))

    # 1-3. 關鍵新聞事件
    key_events = data.get("key_events", [])
    if key_events:
        with st.expander("📌 查看重點新聞事件解析", expanded=False):
            for ev in key_events:
                impact_tag = "🔴 利空" if ev.get("impact") == "negative" else "🟢 利多"
                st.markdown(f"**[{impact_tag}] {ev.get('title')}**")
                st.caption(ev.get("summary"))
                st.divider()

    # 1-4. 風險與潛在機會
    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("⚠️ **主要風險因素**")
        for r in data.get("risk_factors", []):
            st.markdown(f"- {r}")
    with rc2:
        st.markdown("💡 **潛在催化機會**")
        for o in data.get("opportunities", []):
            st.markdown(f"- {o}")


def render_kline_report_ui(data):
    """4. 🤖 K線與技術面報告渲染"""
    if isinstance(data, str):
        st.markdown(data)
        return
    if not isinstance(data, dict):
        return

    rec_map = {"buy": ("🟢 建議買入", "green"), "sell": ("🔴 建議賣出", "red"), "hold": ("🟡 觀望等待", "orange")}
    rec_text, rec_color = rec_map.get(data.get("recommendation", "").lower(), ("⚪ 觀望", "gray"))

    # 4-1. 決策卡片
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 綜合操作建議：:{rec_color}[{rec_text}]")
        st.caption(f"週期對齊狀態：{data.get('timeframe_alignment', '')}")
    with col2:
        st.metric("模型信心度", f"{data.get('confidence', 0)}%")
    with col3:
        indicators = data.get("key_indicators", {})
        st.markdown(f"**趨勢：** {indicators.get('trend', '-')}")
        st.markdown(f"**動能：** {indicators.get('momentum', '-')}")

    st.info(f"**摘要：** {data.get('summary', '')}")

    # 4-2. 各週期詳細分析表格
    per_tf = data.get("per_timeframe_analysis", [])
    if per_tf:
        st.markdown("#### ⏱️ 各週期詳細訊號")
        tf_df = pd.DataFrame([
            {
                "週期": item.get("interval"),
                "訊號": "🟢 多" if item.get("signal") == "buy" else ("🔴 空" if item.get("signal") == "sell" else "🟡 觀望"),
                "推論依據": item.get("reasoning")
            }
            for item in per_tf
        ])
        st.dataframe(tf_df, hide_index=True, use_container_width=True)

    # 4-3. 入場策略與失效位
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"🎯 **入場考量：**\n{data.get('entry_consideration', '')}")
    with c2:
        st.warning(f"🚫 **判斷失效關鍵位：**\n{data.get('invalidation_level', '')}")


def render_social_report_ui(data):
    """6. 🗣️ 社群情緒報告渲染"""
    if isinstance(data, str):
        st.markdown(data)
        return
    if not isinstance(data, dict):
        return

    # 6-1. 情緒統計卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("情緒決策", f"{data.get('recommendation', '').upper()}", f"信心度: {data.get('confidence', 0)}%")
    with col2:
        st.metric("當前情緒狀態", f"{data.get('sentiment_regime', '')}")
    with col3:
        st.metric("社群與指數關係", "背離 (反向訊號)" if "分歧" in data.get("community_alignment", "") else "一致")

    # 6-2. 關鍵反向指標提醒
    st.success(f"💡 **反向指標觀察 (Contrarian Signal)：**\n\n{data.get('contrarian_signal', '')}")

    st.info(f"**摘要：** {data.get('summary', '')}")

    # 6-3. 失效位與風險
    st.markdown(f"🚨 **失效條件：** {data.get('invalidation_level', '')}")
    st.markdown("**主要風險因素：**")
    for r in data.get("risk_factors", []):
        st.markdown(f"- {r}")


# ==========================================
# 🚀 儀表板主渲染邏輯
# ==========================================

def render_dashboard(analysis_result):
    """渲染儀表板整體數據卡片與圖表 (依照指定順序)"""
    st.divider()
    
    # === 0. 讀取數據與設定檔 ===
    tools_config = analysis_result.get("tools_config", {})
    sentiment_config = tools_config.get("sentiment_tools", {})
    tech_config = tools_config.get("tech_tools", {})
    news_config = tools_config.get("news_tools", {})
    
    kline_response = analysis_result.get("kline_response", {})
    if not kline_response and any(tech_config.values()):
        base_symbol = analysis_result.get('symbol', 'BTC').upper()
        symbol_param = base_symbol if base_symbol.endswith("USDT") else f"{base_symbol}USDT"
        kline_response = fetch_technical_data("Dashboard K-Line Fetch", {"symbol": symbol_param})
    
    kline_data = kline_response.get('data', {}) if isinstance(kline_response, dict) else {}
    
    last_15m = get_last_record(kline_data.get("15m_data", []))
    last_1h  = get_last_record(kline_data.get("1h_data", []))
    last_6h  = get_last_record(kline_data.get("6h_data", []))
    last_1d  = get_last_record(kline_data.get("1d_data", []))
    main_last = last_1h if last_1h else (last_15m or last_1d or {})

    raw_social_fg = analysis_result.get('social_fg_data', {})
    fear_greed_data = analysis_result.get('fear_greed') or raw_social_fg.get('fear_greed', {})
    social_data = analysis_result.get('long_short') or raw_social_fg.get('long_short', {})

    # ==========================================
    # 1. 📰 新聞報告
    # ==========================================
    news_report = analysis_result.get("news_report")
    if news_config.get("news") and news_report:
        st.subheader("📰 新聞分析報告")
        render_news_report_ui(news_report)
        st.divider()

    # ==========================================
    # 2. 📊 技術 Chart (數據表格)
    # ==========================================
    if any(tech_config.values()):
        st.subheader("📊 技術指標最新數據")
        col1, col2 = st.columns(2)
        
        with col1:
            if tech_config.get("ma"):
                st.markdown("#### 移動平均線 (MA - 1h)")
                st.dataframe(pd.DataFrame({
                    '週期': ['MA 7', 'MA 25', 'MA 99'],
                    '數值': [
                        f"${main_last.get('ma_7', main_last.get('ma7', 0)):,.2f}",
                        f"${main_last.get('ma_25', main_last.get('ma25', 0)):,.2f}",
                        f"${main_last.get('ma_99', main_last.get('ma99', 0)):,.2f}"
                    ]
                }), hide_index=True, use_container_width=True)
                
            if tech_config.get("ema"):
                st.markdown("#### 指數移動平均線 (EMA - 1h)")
                st.dataframe(pd.DataFrame({
                    '週期': ['EMA 7', 'EMA 25', 'EMA 99'],
                    '數值': [
                        f"${main_last.get('ema_7', main_last.get('ema7', 0)):,.2f}",
                        f"${main_last.get('ema_25', main_last.get('ema25', 0)):,.2f}",
                        f"${main_last.get('ema_99', main_last.get('ema99', 0)):,.2f}"
                    ]
                }), hide_index=True, use_container_width=True)
                
        with col2:
            if tech_config.get("bollinger"):
                st.markdown("#### 布林通道 (Bollinger Bands - 1h)")
                bb_upper = main_last.get('upper', main_last.get('bb_upper', 0))
                bb_middle = main_last.get('middle', main_last.get('bb_middle', 0))
                bb_lower = main_last.get('lower', main_last.get('bb_lower', 0))
                
                st.dataframe(pd.DataFrame({
                    '指標': ['上軌', '中軌', '下軌'],
                    '數值': [f"${bb_upper:,.2f}", f"${bb_middle:,.2f}", f"${bb_lower:,.2f}"]
                }), hide_index=True, use_container_width=True)

            st.markdown("#### 各週期最新RSI")
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
    # 3. 📈 K線圖
    # ==========================================
    if any(tech_config.values()):
        st.subheader("📈 多週期互動式 K 線圖")
        tab_15m, tab_1h, tab_6h, tab_1d = st.tabs(["超短期 (15m)", "短期 (1h)", "中期 (6h)", "長期 (1d)"])
        
        try:
            base_symbol = analysis_result.get('symbol', 'BTC').upper()
            risk = analysis_result.get('risk_level', '低')

            with tab_15m:
                df_15m = pd.DataFrame(kline_data.get("15m_data", [])[-50:])
                if not df_15m.empty:
                    st.plotly_chart(create_candlestick_chart(df_15m, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 15m K 線數據")

            with tab_1h:
                df_1h = pd.DataFrame(kline_data.get("1h_data", [])[-50:])
                if not df_1h.empty:
                    st.plotly_chart(create_candlestick_chart(df_1h, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 1h K 線數據")
                    
            with tab_6h:
                df_6h = pd.DataFrame(kline_data.get("6h_data", [])[-50:])
                if not df_6h.empty:
                    st.plotly_chart(create_candlestick_chart(df_6h, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 6h K 線數據")
                    
            with tab_1d:
                df_1d = pd.DataFrame(kline_data.get("1d_data", [])[-50:])
                if not df_1d.empty:
                    st.plotly_chart(create_candlestick_chart(df_1d, base_symbol, risk), use_container_width=True)
                else:
                    st.info("無 1d K 線數據")
                    
        except Exception as e:
            st.error(f"❌ 繪製 K 線圖失敗: {str(e)}")

        st.divider()

    # ==========================================
    # 4. 🤖 K線報告
    # ==========================================
    kline_report = analysis_result.get("kline_report")
    if any(tech_config.values()) and kline_report:
        st.subheader("📈 技術分析報告")
        render_kline_report_ui(kline_report)
        st.divider()

    # ==========================================
    # 5. 🎯 半圓圖表
    # ==========================================
    active_gauges = []
    if sentiment_config.get("fear_greed") and fear_greed_data:
        fg_val = fear_greed_data.get('value', 50) if isinstance(fear_greed_data, dict) else fear_greed_data
        active_gauges.append((float(fg_val), "恐懼貪婪指數"))
        
    if sentiment_config.get("long_short") and social_data:
        up_val = social_data.get('up', 50) if isinstance(social_data, dict) else social_data
        active_gauges.append((float(up_val), "社群看多比例"))
        
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
    # 6. 🗣️ 社群報告
    # ==========================================
    social_report = analysis_result.get("social_report")
    if (sentiment_config.get("fear_greed") or sentiment_config.get("long_short")) and social_report:
        st.subheader("🗣️ 社群情緒分析報告")
        render_social_report_ui(social_report)
        st.divider()
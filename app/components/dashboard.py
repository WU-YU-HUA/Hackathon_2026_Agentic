# app/components/dashboard.py
import streamlit as st
import pandas as pd
from app.components.charts import create_gauge_chart, create_candlestick_chart
from api.getData import CryptoData

def render_dashboard(analysis_result):
    """渲染儀表板整體數據卡片與圖表 (支援動態開關設定)"""
    st.divider()
    
    # === 0. 讀取側邊欄設定檔 ===
    tools_config = analysis_result.get("tools_config", {})
    sentiment_config = tools_config.get("sentiment_tools", {})
    tech_config = tools_config.get("tech_tools", {})
    
    tech_data = analysis_result.get('tech_data', {})
    fear_greed_data = analysis_result.get('fear_greed', {})
    social_data = analysis_result.get('social', {})
    
    # ==========================================
    # === 1. 技術數據表格 (2x2 佈局) ===
    # ==========================================
    # 只要有勾選任何技術指標才顯示這個區塊
    if any(tech_config.values()):
        st.subheader("📊 技術指標數據")
        col1, col2 = st.columns(2)
        
        with col1:
            # 1-1. 移動平均線 (MA)
            if tech_config.get("ma"):
                st.markdown("#### 移動平均線 (MA)")
                ma_data = tech_data.get('ma', {})
                if ma_data:
                    st.dataframe(pd.DataFrame({
                        '週期': ['MA 7', 'MA 25', 'MA 99'],
                        '數值': [
                            f"${ma_data.get('ma_7', 0):,.2f}",
                            f"${ma_data.get('ma_25', 0):,.2f}",
                            f"${ma_data.get('ma_99', 0):,.2f}"
                        ]
                    }), hide_index=True, use_container_width=True)
                else:
                    st.info("無 MA 數據")
                
            # 1-2. 指數移動平均線 (EMA)
            if tech_config.get("ema"):
                st.markdown("#### 指數移動平均線 (EMA)")
                ema_data = tech_data.get('ema', {})
                if ema_data:
                    st.dataframe(pd.DataFrame({
                        '週期': ['EMA 7', 'EMA 25', 'EMA 99'],
                        '數值': [
                            f"${ema_data.get('ema_7', 0):,.2f}",
                            f"${ema_data.get('ema_25', 0):,.2f}",
                            f"${ema_data.get('ema_99', 0):,.2f}"
                        ]
                    }), hide_index=True, use_container_width=True)
                else:
                    st.info("無 EMA 數據")
                
        with col2:
            # 2-1. 布林通道 (Bollinger Bands)
            if tech_config.get("bollinger"):
                st.markdown("#### 布林通道 (Bollinger Bands)")
                bb_data = tech_data.get('bollinger_bands', {})
                if bb_data:
                    st.dataframe(pd.DataFrame({
                        '指標': ['上軌', '中軌', '下軌'],
                        '數值': [
                            f"${bb_data.get('upper', 0):,.2f}",
                            f"${bb_data.get('middle', 0):,.2f}",
                            f"${bb_data.get('lower', 0):,.2f}"
                        ]
                    }), hide_index=True, use_container_width=True)
                    st.caption(f"視窗: {bb_data.get('window', 20)} | 標準差倍數: {bb_data.get('dev', 2)}")
                else:
                    st.info("無布林通道數據")

            # 2-2. 其他指標 (動態組合)
            st.markdown("#### 綜合數據")
            # 預設一定有價格和時間範圍
            indicators_labels = ['當前價格']
            indicators_values = [f"${tech_data.get('price', 0):,.2f}"]
            
            # 如果有勾選 RSI，才把 RSI 塞進表格
            if tech_config.get("rsi") and tech_data.get('rsi'):
                indicators_labels.append('RSI')
                indicators_values.append(f"{tech_data.get('rsi', {}).get('value', 0):.2f}")
                
            indicators_labels.append('時間範圍')
            indicators_values.append(tech_data.get('interval', 'N/A'))

            st.dataframe(pd.DataFrame({
                '指標': indicators_labels,
                '數值': indicators_values
            }), hide_index=True, use_container_width=True)

        st.divider()

    # ==========================================
    # === 2. 半圓儀表盤群 (動態欄位排版) ===
    # ==========================================
    # 收集需要畫出來的儀表盤清單
    active_gauges = []
    
    if sentiment_config.get("fear_greed") and fear_greed_data:
        fg_val = fear_greed_data.get('value', 50) if isinstance(fear_greed_data, dict) else 50
        active_gauges.append((fg_val, "恐懼貪婪指數"))
        
    if sentiment_config.get("long_short") and social_data:
        up_val = social_data.get('up', 50)
        active_gauges.append((up_val, "社群看多比例"))
        
    if tech_config.get("rsi") and tech_data.get("rsi"):
        rsi_val = tech_data.get('rsi', {}).get('value', 50)
        active_gauges.append((rsi_val, "RSI 指標"))

    # 如果有任何儀表盤需要畫，才渲染這個區塊
    if active_gauges:
        st.subheader("📊 市場情緒指標")

        # 動態切割欄位：如果有 2 個儀表盤，就完美切成兩半
        cols = st.columns(len(active_gauges))
        
        for idx, (val, title) in enumerate(active_gauges):
            with cols[idx]:
                st.plotly_chart(create_gauge_chart(val, title), use_container_width=True)
                
        st.divider()

    # ==========================================
    # === 3. 多週期 K 線圖 (支援 1h, 6h, 1d) ===
    # ==========================================
    st.subheader("📈 多週期互動式 K 線圖")
    
    # 建立三個分頁標籤
    tab_1h, tab_6h, tab_1d = st.tabs(["短期 (1h線)", "中期 (6h線)", "長期 (日線)"])
    
    try:
        crypto_data = CryptoData()
        symbol_lower = analysis_result['pair'].lower()
        base_symbol = analysis_result['symbol']
        risk = analysis_result['risk_level']
        
        with tab_1h:
            # 1h 線看過去 7 天
            df_1h = crypto_data.get_history_df(symbol=symbol_lower, interval="1h", period=7)
            if not df_1h.empty:
                st.plotly_chart(create_candlestick_chart(df_1h, base_symbol, risk), use_container_width=True)
                
        with tab_6h:
            # 6h 線看過去 30 天
            df_6h = crypto_data.get_history_df(symbol=symbol_lower, interval="6h", period=30)
            if not df_6h.empty:
                st.plotly_chart(create_candlestick_chart(df_6h, base_symbol, risk), use_container_width=True)
                
        with tab_1d:
            # 1d 線看過去 90 天
            df_1d = crypto_data.get_history_df(symbol=symbol_lower, interval="1d", period=90)
            if not df_1d.empty:
                st.plotly_chart(create_candlestick_chart(df_1d, base_symbol, risk), use_container_width=True)
                
    except Exception as e:
        st.error(f"❌ 繪製 K 線圖失敗: {str(e)}")

    st.divider()

    # ==========================================
    # === 4. 自訂進出場策略 (預留區塊) ===
    # ==========================================
    st.subheader("🎯 專屬量化策略：布林通道動態判定")
    
    # 這裡預留讀取你未來的策略結果
    custom_strategy_result = analysis_result.get("custom_bb_strategy")
    
    if custom_strategy_result:
        # 未來接上後，這裡可以漂亮地顯示買賣點與建議
        st.json(custom_strategy_result) # 暫時用 json 顯示，之後可以改成漂亮的 metric 或 markdown
    else:
        # 目前尚未接上時的顯示畫面
        st.info("🚧 這裡預留給您自訂的「布林通道出入場策略」。未來串接後，將在此顯示具體的買賣點與訊號。")
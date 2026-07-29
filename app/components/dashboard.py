# app/components/dashboard.py
import streamlit as st
import pandas as pd
from app.components.charts import create_gauge_chart, create_candlestick_chart
from api.getData import CryptoData

def render_dashboard(analysis_result):
    """渲染儀表板整體數據卡片與圖表"""
    st.divider()
    st.subheader("📊 技術指標數據")
    
    tech_data = analysis_result.get('tech_data', {})
    fear_greed_data = analysis_result.get('fear_greed', {})
    social_data = analysis_result.get('social', {})
    
    # === 1. 技術數據表格 (2x2 佈局) ===
    col1, col2 = st.columns(2)
    
    with col1:
        # 1-1. 移動平均線 (MA)
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

        # 2-2. 其他指標
        st.markdown("#### 其他指標")
        st.dataframe(pd.DataFrame({
            '指標': ['當前價格', 'RSI', '時間範圍'],
            '數值': [
                f"${tech_data.get('price', 0):,.2f}",
                f"{tech_data.get('rsi', {}).get('value', 0):.2f}",
                tech_data.get('interval', 'N/A')
            ]
        }), hide_index=True, use_container_width=True)

    st.divider()

    # === 2. 半圓儀表盤群 ===
    st.subheader("📊 市場情緒指標")
    g1, g2, g3 = st.columns(3)
    
    with g1:
        fg_val = fear_greed_data.get('value', 50) if isinstance(fear_greed_data, dict) else 50
        st.plotly_chart(create_gauge_chart(fg_val, "恐懼貪婪指數"), use_container_width=True)
    with g2:
        up_val = social_data.get('up', 50) if social_data else 50
        st.plotly_chart(create_gauge_chart(up_val, "社群看多比例"), use_container_width=True)
    with g3:
        rsi_val = tech_data.get('rsi', {}).get('value', 50)
        st.plotly_chart(create_gauge_chart(rsi_val, "RSI 指標"), use_container_width=True)

    st.divider()

    # === 3. K 線圖 ===
    st.subheader("📈 互動式 K 線圖")
    try:
        crypto_data = CryptoData()
        history_df = crypto_data.get_history_df(symbol=analysis_result['pair'].lower(), interval="1h", period=7)
        if not history_df.empty:
            fig = create_candlestick_chart(history_df, analysis_result['symbol'], analysis_result['risk_level'])
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ 繪製 K 線圖失敗: {str(e)}")
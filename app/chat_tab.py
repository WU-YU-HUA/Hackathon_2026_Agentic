import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import sys

# 添加 api 資料夾到路徑
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api'))

from api.getData import CryptoData
from api.fearGreed import FearGreedData
from api.social import coinGeckoVote
from api.symbol_mapping import get_coingecko_id

def create_gauge_chart(value, title, color_scheme="fear_greed"):
    """
    創建半圓儀表盤
    
    :param value: 數值 (0-100)
    :param title: 圖表標題
    :param color_scheme: 配色方案 ('fear_greed' 或 'sentiment')
    """
    if color_scheme == "fear_greed":
        # 恐懼貪婪指數配色 (0=極度恐懼紅色, 100=極度貪婪綠色)
        colors = ['#d32f2f', '#f57c00', '#fbc02d', '#7cb342', '#388e3c']
        threshold_steps = [0, 25, 50, 75, 100]
    else:
        # 多空投票配色 (0=極度看空, 100=極度看多)
        colors = ['#d32f2f', '#f57c00', '#fbc02d', '#7cb342', '#388e3c']
        threshold_steps = [0, 25, 50, 75, 100]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        number={'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "darkblue", 'thickness': 0.25},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [threshold_steps[0], threshold_steps[1]], 'color': colors[0]},
                {'range': [threshold_steps[1], threshold_steps[2]], 'color': colors[1]},
                {'range': [threshold_steps[2], threshold_steps[3]], 'color': colors[2]},
                {'range': [threshold_steps[3], threshold_steps[4]], 'color': colors[3]},
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin={'t': 50, 'b': 0, 'l': 20, 'r': 20},
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"}
    )
    
    return fig

def get_allowed_pairs():
    """從 .env 讀取允許的交易對"""
    max_pairs_str = os.getenv("MAX_PAIRS", '["BTCUSDT"]')
    try:
        pairs = json.loads(max_pairs_str)
        return pairs
    except:
        return ["BTCUSDT"]

def render_chat_tab(tools_config):
    """渲染 Tab 1: AI 對話與分析"""
    st.header("AI 助手對話介面")
    
    # 初始化session state變數
    if 'risk_level' not in st.session_state:
        st.session_state.risk_level = None
    if 'selected_pair' not in st.session_state:
        st.session_state.selected_pair = None
    
    trading_persona = st.session_state.trading_persona
    
    # 步驟 1: 詢問風險等級
    if st.session_state.risk_level is None:
        st.subheader("📊 風險評估")
        st.write("請選擇您可接受的風險等級：")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("🟢 1\n極低風險", use_container_width=True):
                st.session_state.risk_level = 1
                st.session_state.chat_history.append({"role": "user", "content": "我選擇風險等級: 1 (極低風險)"})
                st.session_state.chat_history.append({"role": "assistant", "content": "了解！您選擇了極低風險等級。接下來請選擇想要分析的交易對。"})
                st.rerun()
        
        with col2:
            if st.button("🟡 2\n低風險", use_container_width=True):
                st.session_state.risk_level = 2
                st.session_state.chat_history.append({"role": "user", "content": "我選擇風險等級: 2 (低風險)"})
                st.session_state.chat_history.append({"role": "assistant", "content": "了解！您選擇了低風險等級。接下來請選擇想要分析的交易對。"})
                st.rerun()
        
        with col3:
            if st.button("🟠 3\n中等風險", use_container_width=True):
                st.session_state.risk_level = 3
                st.session_state.chat_history.append({"role": "user", "content": "我選擇風險等級: 3 (中等風險)"})
                st.session_state.chat_history.append({"role": "assistant", "content": "了解！您選擇了中等風險等級。接下來請選擇想要分析的交易對。"})
                st.rerun()
        
        with col4:
            if st.button("🟠 4\n高風險", use_container_width=True):
                st.session_state.risk_level = 4
                st.session_state.chat_history.append({"role": "user", "content": "我選擇風險等級: 4 (高風險)"})
                st.session_state.chat_history.append({"role": "assistant", "content": "了解！您選擇了高風險等級。接下來請選擇想要分析的交易對。"})
                st.rerun()
        
        with col5:
            if st.button("🔴 5\n極高風險", use_container_width=True):
                st.session_state.risk_level = 5
                st.session_state.chat_history.append({"role": "user", "content": "我選擇風險等級: 5 (極高風險)"})
                st.session_state.chat_history.append({"role": "assistant", "content": "了解！您選擇了極高風險等級。接下來請選擇想要分析的交易對。"})
                st.rerun()
        
        st.info("💡 風險等級說明：\n- 1-2: 保守型，適合長期持有\n- 3: 平衡型，中期交易\n- 4-5: 激進型，短期高風險交易")
        return
    
    # 步驟 2: 選擇交易對
    if st.session_state.selected_pair is None:
        st.subheader("💱 選擇交易對")
        st.write(f"您的風險等級: **{st.session_state.risk_level}**")
        
        allowed_pairs = get_allowed_pairs()
        st.write("請選擇想要分析的交易對：")
        
        # 根據交易對數量動態調整欄位
        cols = st.columns(min(len(allowed_pairs), 5))
        
        for idx, pair in enumerate(allowed_pairs):
            col_idx = idx % 5
            with cols[col_idx]:
                # 提取幣種名稱（例如：BTCUSDT -> BTC）
                symbol = pair.replace("USDT", "").replace("TWD", "")
                if st.button(f"📈 {symbol}", key=f"pair_{pair}", use_container_width=True):
                    st.session_state.selected_pair = pair
                    st.session_state.current_symbol = symbol
                    st.session_state.chat_history.append({"role": "user", "content": f"我想分析 {symbol}"})
                    st.session_state.chat_history.append({"role": "assistant", "content": f"好的！正在為您分析 {symbol}，請稍候..."})
                    st.rerun()
        
        if st.button("🔄 重新選擇風險等級", use_container_width=True):
            st.session_state.risk_level = None
            st.rerun()
        
        return
    
    # 步驟 3: 顯示對話歷史和分析結果
    st.write(f"**風險等級**: {st.session_state.risk_level} | **交易對**: {st.session_state.selected_pair}")
    
    if st.button("🔄 重新開始", use_container_width=True):
        st.session_state.risk_level = None
        st.session_state.selected_pair = None
        st.session_state.show_dashboard = False
        st.session_state.analysis_result = None
        st.rerun()
    
    # 對話歷史顯示
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.chat_message("user").write(chat["content"])
            else:
                st.chat_message("assistant").write(chat["content"])
    
    # 如果還沒有分析結果，自動生成
    if not st.session_state.show_dashboard and st.session_state.selected_pair:
        detected_symbol = st.session_state.current_symbol
        selected_pair = st.session_state.selected_pair
        
        with st.spinner(f'正在獲取 {detected_symbol} 的數據...'):
            try:
                # 1. 獲取技術指標數據
                crypto_data = CryptoData()
                tech_data = crypto_data.get_technical_data(
                    symbol=selected_pair.lower(),
                    interval="1h",
                    period=100  # 增加天數以確保有足夠數據計算 MA99
                )
                
                # 2. 獲取恐懼貪婪指數
                fear_greed_api = FearGreedData(limit=1)
                fear_greed_data = fear_greed_api.get_raw_data()
                
                # 3. 獲取社群投票數據
                coingecko_id = get_coingecko_id(detected_symbol)
                social_data = coinGeckoVote(coingecko_id)
                
                # 檢查是否有錯誤
                if "error" in tech_data:
                    st.error(f"❌ 獲取技術數據失敗: {tech_data['error']}")
                    return
                
                ai_response = f"已為您分析 {detected_symbol}，請參考以下儀表板："
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
                # 儲存數據到 session state
                st.session_state.analysis_result = {
                    "symbol": detected_symbol,
                    "pair": selected_pair,
                    "risk_level": st.session_state.risk_level,
                    "tech_data": tech_data,
                    "fear_greed": fear_greed_data,
                    "social": social_data,
                    "coingecko_id": coingecko_id,
                }
                st.session_state.show_dashboard = True
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 獲取數據時發生錯誤: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
                return
    
    # 使用者輸入
    user_input = st.chat_input("繼續對話或輸入其他問題")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 檢查是否要切換交易對
        allowed_pairs = get_allowed_pairs()
        detected_symbol = None
        
        for pair in allowed_pairs:
            symbol = pair.replace("USDT", "").replace("TWD", "")
            if symbol.upper() in user_input.upper():
                detected_symbol = symbol
                st.session_state.selected_pair = pair
                st.session_state.current_symbol = symbol
                st.session_state.show_dashboard = False
                break
        
        if detected_symbol:
            ai_response = f"好的！正在切換到 {detected_symbol} 的分析..."
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            st.rerun()
        else:
            # 一般對話回應
            ai_response = f"我收到您的訊息：「{user_input}」。目前正在分析 {st.session_state.current_symbol}。如需切換幣種，請輸入幣種名稱（如：BTC、ETH、SOL等）。"
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            st.rerun()
    
    
    # 顯示儀表板
    if st.session_state.show_dashboard and st.session_state.analysis_result:
        st.divider()
        st.subheader("📊 即時分析儀表板")
        
        result = st.session_state.analysis_result
        tech_data = result.get('tech_data', {})
        fear_greed_data = result.get('fear_greed', {})
        social_data = result.get('social', {})
        
        # === Dashboard 1: 技術指標數據 ===
        st.subheader("� 技術指標數據")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 移動平均線 (MA)")
            ma_data = tech_data.get('ma', {})
            if ma_data:
                ma_df = pd.DataFrame({
                    '週期': ['MA 7', 'MA 25', 'MA 99'],
                    '數值': [
                        f"${ma_data.get('ma_7', 0):,.2f}",
                        f"${ma_data.get('ma_25', 0):,.2f}",
                        f"${ma_data.get('ma_99', 0):,.2f}"
                    ]
                })
                st.dataframe(ma_df, hide_index=True, use_container_width=True)
            else:
                st.info("無 MA 數據")
            
            st.markdown("#### 指數移動平均線 (EMA)")
            ema_data = tech_data.get('ema', {})
            if ema_data:
                ema_df = pd.DataFrame({
                    '週期': ['EMA 7', 'EMA 25', 'EMA 99'],
                    '數值': [
                        f"${ema_data.get('ema_7', 0):,.2f}",
                        f"${ema_data.get('ema_25', 0):,.2f}",
                        f"${ema_data.get('ema_99', 0):,.2f}"
                    ]
                })
                st.dataframe(ema_df, hide_index=True, use_container_width=True)
            else:
                st.info("無 EMA 數據")
        
        with col2:
            st.markdown("#### 布林通道 (Bollinger Bands)")
            bb_data = tech_data.get('bollinger_bands', {})
            if bb_data:
                bb_df = pd.DataFrame({
                    '指標': ['上軌', '中軌', '下軌'],
                    '數值': [
                        f"${bb_data.get('upper', 0):,.2f}",
                        f"${bb_data.get('middle', 0):,.2f}",
                        f"${bb_data.get('lower', 0):,.2f}"
                    ]
                })
                st.dataframe(bb_df, hide_index=True, use_container_width=True)
                st.caption(f"視窗: {bb_data.get('window', 20)} | 標準差倍數: {bb_data.get('dev', 2)}")
            else:
                st.info("無布林通道數據")
            
            st.markdown("#### 其他指標")
            other_df = pd.DataFrame({
                '指標': ['當前價格', 'RSI', '時間範圍'],
                '數值': [
                    f"${tech_data.get('price', 0):,.2f}",
                    f"{tech_data.get('rsi', {}).get('value', 0):.2f}",
                    tech_data.get('interval', 'N/A')
                ]
            })
            st.dataframe(other_df, hide_index=True, use_container_width=True)
        
        st.divider()
        
        # === Dashboard 2 & 3: 半圓儀表盤 ===
        st.subheader("📊 市場情緒指標")
        
        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
        
        with gauge_col1:
            # Dashboard 2: 恐懼貪婪指數
            if 'error' not in fear_greed_data:
                fg_value = fear_greed_data.get('value', 50)
                fg_sentiment = fear_greed_data.get('sentiment', 'Neutral')
                
                fig_fg = create_gauge_chart(fg_value, "恐懼貪婪指數", "fear_greed")
                st.plotly_chart(fig_fg, use_container_width=True)
                
                st.markdown(f"""
                <div style='text-align: center; padding: 10px;'>
                    <h4>當前情緒: {fg_sentiment}</h4>
                    <p style='color: gray;'>數值: {fg_value}/100</p>
                    <p style='color: gray;'>資料來源: Alternative.me</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ 無法獲取恐懼貪婪指數")
        
        with gauge_col2:
            # Dashboard 3: 社群多空投票
            if social_data and 'up' in social_data:
                social_up = social_data.get('up', 50)
                social_down = social_data.get('down', 50)
                
                fig_social = create_gauge_chart(social_up, "社群看多比例", "sentiment")
                st.plotly_chart(fig_social, use_container_width=True)
                
                st.markdown(f"""
                <div style='text-align: center; padding: 10px;'>
                    <h4>看多: {social_up:.1f}% | 看空: {social_down:.1f}%</h4>
                    <p style='color: gray;'>資料來源: CoinGecko</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ 無法獲取社群投票數據")
        
        with gauge_col3:
            # RSI 指標儀表盤
            rsi_value = tech_data.get('rsi', {}).get('value', 50)
            fig_rsi = create_gauge_chart(rsi_value, "RSI 相對強弱指標", "fear_greed")
            st.plotly_chart(fig_rsi, use_container_width=True)
            
            rsi_status = "超買" if rsi_value > 70 else "超賣" if rsi_value < 30 else "正常"
            st.markdown(f"""
            <div style='text-align: center; padding: 10px;'>
                <h4>狀態: {rsi_status}</h4>
                <p style='color: gray;'>RSI {rsi_value:.1f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # === K 線圖 ===
        st.subheader("📈 互動式 K 線圖")
        
        # 使用真實歷史數據繪製 K 線圖
        try:
            crypto_data = CryptoData()
            history_df = crypto_data.get_history_df(
                symbol=result['pair'].lower(),
                interval="1h",
                period=7  # 最近7天數據
            )
            
            if not history_df.empty:
                # 轉換時間戳
                history_df['datetime'] = pd.to_datetime(history_df['timestamp'], unit='s')
                
                # 創建 K 線圖
                fig = go.Figure(data=[go.Candlestick(
                    x=history_df['datetime'],
                    open=history_df['open'],
                    high=history_df['high'],
                    low=history_df['low'],
                    close=history_df['close'],
                    name=result['symbol']
                )])
                
                # 添加 MA 線
                if 'ma_7' in history_df.columns:
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['ma_7'], 
                        name='MA7', 
                        line=dict(color='cyan', width=1)
                    ))
                if 'ma_25' in history_df.columns:
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['ma_25'], 
                        name='MA25', 
                        line=dict(color='yellow', width=1)
                    ))
                
                # 添加 EMA 線
                if 'ema_7' in history_df.columns:
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['ema_7'], 
                        name='EMA7', 
                        line=dict(color='lightgreen', width=1, dash='dot')
                    ))
                if 'ema_25' in history_df.columns:
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['ema_25'], 
                        name='EMA25', 
                        line=dict(color='orange', width=1, dash='dot')
                    ))
                
                # 添加布林通道
                if 'bb_upper' in history_df.columns:
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['bb_upper'], 
                        name='布林上軌', 
                        line=dict(color='rgba(250, 128, 114, 0.5)', dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['bb_middle'], 
                        name='布林中軌', 
                        line=dict(color='orange')
                    ))
                    fig.add_trace(go.Scatter(
                        x=history_df['datetime'], 
                        y=history_df['bb_lower'], 
                        name='布林下軌', 
                        line=dict(color='rgba(135, 206, 250, 0.5)', dash='dash')
                    ))
                
                fig.update_layout(
                    title=f"{result['symbol']}/USDT - 風險等級 {result['risk_level']}",
                    yaxis_title="價格 (USD)",
                    xaxis_title="時間",
                    template="plotly_dark",
                    height=600,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ 無法獲取歷史 K 線數據")
        except Exception as e:
            st.error(f"❌ 繪製 K 線圖時發生錯誤: {str(e)}")
        
        st.divider()
        
        # === 預留空間：Agent 分析報告 ===
        st.subheader("🤖 AI 分析報告")
        st.info("💡 此區域預留給 Agent 生成的分析報告")
        
        # TODO: 在此處顯示 Agent 生成的報告
        # 可以使用 st.session_state.agent_report 來存儲報告內容
        if 'agent_report' in st.session_state and st.session_state.agent_report:
            st.markdown(st.session_state.agent_report)
        else:
            st.write("報告尚未生成，請等待 Agent 分析完成...")
        
        st.divider()
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

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
        
        ai_response = f"已為您分析 {detected_symbol}，請參考以下儀表板："
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
        # 根據幣種設定不同的價格範圍
        if detected_symbol == "BTC":
            current_price = np.random.uniform(40000, 70000)
        elif detected_symbol == "ETH":
            current_price = np.random.uniform(2000, 4000)
        elif detected_symbol == "SOL":
            current_price = np.random.uniform(20, 200)
        elif detected_symbol == "BNB":
            current_price = np.random.uniform(200, 600)
        elif detected_symbol == "XRP":
            current_price = np.random.uniform(0.3, 2)
        else:
            current_price = np.random.uniform(10, 1000)
            
        change_24h = np.random.uniform(-5, 10)
        rsi = np.random.uniform(30, 80)
        
        # 根據風險等級和交易人格調整共識評分和建議
        risk_factor = st.session_state.risk_level / 5.0  # 0.2 ~ 1.0
        
        if trading_persona == "Degen":
            base_score = np.random.randint(70, 85)
            confluence_score = int(base_score + (risk_factor * 10))
            recommendation = "🚀 買進" if confluence_score > 70 else "⏳ 觀望"
        else:
            base_score = np.random.randint(50, 70)
            confluence_score = int(base_score + (risk_factor * 5))
            recommendation = "⏳ 觀望" if confluence_score < 70 else "🚀 買進"
        
        st.session_state.analysis_result = {
            "symbol": detected_symbol,
            "pair": st.session_state.selected_pair,
            "price": current_price,
            "change_24h": change_24h,
            "rsi": rsi,
            "confluence_score": min(confluence_score, 100),
            "recommendation": recommendation,
            "risk_level": st.session_state.risk_level,
            "bollinger_enabled": tools_config["bollinger"],
            "ma_enabled": tools_config["ma"],
            "sentiment_enabled": tools_config["sentiment"]
        }
        st.session_state.show_dashboard = True
        st.rerun()
    
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
        st.subheader("📊 即時分析儀表板 (Dashboard)")
        
        result = st.session_state.analysis_result
        
        # 顯示風險等級
        risk_labels = {1: "極低風險", 2: "低風險", 3: "中等風險", 4: "高風險", 5: "極高風險"}
        risk_colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🟠", 5: "🔴"}
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("當前價格", f"${result['price']:,.2f}", f"{result['change_24h']:+.2f}%")
        col2.metric("RSI 指標", f"{result['rsi']:.1f}")
        col3.metric("共識評分", f"{result['confluence_score']}/100")
        col4.metric("建議動作", result['recommendation'])
        col5.metric("風險等級", f"{risk_colors[result['risk_level']]} {result['risk_level']}")
        
        st.subheader("📈 互動式 K 線圖")
        dates = pd.date_range(end=datetime.now(), periods=60, freq='h')
        base_price = result['price']
        
        np.random.seed(42)
        opens = base_price + np.random.randn(60).cumsum() * (base_price * 0.01)
        closes = opens + np.random.randn(60) * (base_price * 0.005)
        highs = np.maximum(opens, closes) + np.abs(np.random.randn(60) * (base_price * 0.003))
        lows = np.minimum(opens, closes) - np.abs(np.random.randn(60) * (base_price * 0.003))
        
        fig = go.Figure(data=[go.Candlestick(
            x=dates, open=opens, high=highs, low=lows, close=closes, name=result['symbol']
        )])
        
        if result['bollinger_enabled']:
            ma20 = pd.Series(closes).rolling(20).mean()
            std20 = pd.Series(closes).rolling(20).std()
            fig.add_trace(go.Scatter(x=dates, y=ma20 + (std20 * 2), name='布林上軌', line=dict(color='rgba(250, 128, 114, 0.5)', dash='dash')))
            fig.add_trace(go.Scatter(x=dates, y=ma20, name='MA20 (中軌)', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=dates, y=ma20 - (std20 * 2), name='布林下軌', line=dict(color='rgba(135, 206, 250, 0.5)', dash='dash')))
        
        if result['ma_enabled']:
            fig.add_trace(go.Scatter(x=dates, y=pd.Series(closes).rolling(7).mean(), name='MA7', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=dates, y=pd.Series(closes).rolling(25).mean(), name='MA25', line=dict(color='blue')))
        
        fig.update_layout(
            title=f"{result['symbol']}/USDT - 風險等級 {result['risk_level']}",
            yaxis_title="價格 (USD)",
            xaxis_title="時間",
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📝 綜合分析報告")
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # 根據風險等級調整分析建議
            risk_advice = {
                1: "建議保守操作，優先選擇市值前10的穩定幣種",
                2: "可適度參與，但建議設定較小的止損點",
                3: "可正常操作，但需密切關注市場動態",
                4: "適合有經驗的交易者，需做好風控",
                5: "高風險高報酬，建議僅用閒錢操作"
            }
            
            st.markdown(f"""
### 各項指標貢獻度
            
| 指標 | 評分 | 權重 |
|------|------|------|
| 布林通道 | {np.random.randint(60, 80)}/100 | 30% |
| 移動平均線 | {np.random.randint(70, 90)}/100 | 35% |
| 社群情緒 | {np.random.randint(65, 85)}/100 | 35% |

**最終共識評分**: {result['confluence_score']}/100

**風險等級**: {risk_colors[result['risk_level']]} {risk_labels[result['risk_level']]}

**建議動作**: {result['recommendation']}

**理由**: {'社群情緒強勁，價格突破中軌，短線機會明確' if trading_persona == 'Degen' else '趨勢向上但需等待回調，建議觀望或小倉位進場'}

**風險提示**: {risk_advice[result['risk_level']]}

---
*根據 {trading_persona} 交易人格與風險等級 {result['risk_level']} 生成*
            """)
        
        with col_right:
            st.info("💡 **操作建議**")
            if "買進" in result['recommendation']:
                st.success(f"✅ 建議買進 {result['symbol']}")
                st.write(f"**建議價格**: ${result['price']:,.2f}")
                
                # 根據風險等級建議倉位
                position_advice = {
                    1: "5-10%",
                    2: "10-15%",
                    3: "10-20%",
                    4: "15-25%",
                    5: "20-30%"
                }
                st.write(f"**建議倉位**: {position_advice[result['risk_level']]} 資金")
                
                if st.button("🎯 前往下單", key="go_to_order"):
                    st.success("請切換至「模擬下單」頁籤")
            else:
                st.warning("⏳ 建議觀望")
                st.write("等待更好的進場時機")
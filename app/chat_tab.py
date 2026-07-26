import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

def render_chat_tab(tools_config):
    """渲染 Tab 1: AI 對話與分析"""
    st.header("AI 助手對話介面")
    
    trading_persona = st.session_state.trading_persona
    
    # 對話歷史顯示
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.chat_message("user").write(chat["content"])
            else:
                st.chat_message("assistant").write(chat["content"])
    
    # 使用者輸入
    user_input = st.chat_input("輸入加密貨幣代號進行分析（如：BTC、ETH、SOL）")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        crypto_symbols = ["BTC", "ETH", "SOL", "DOGE", "MATIC", "AVAX", "ADA", "DOT"]
        detected_symbol = None
        for symbol in crypto_symbols:
            if symbol.upper() in user_input.upper():
                detected_symbol = symbol
                break
        
        if detected_symbol:
            st.session_state.current_symbol = detected_symbol
            
            ai_response = f"已為您分析 {detected_symbol}，請參考以下儀表板："
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            
            current_price = np.random.uniform(40000, 70000) if detected_symbol == "BTC" else np.random.uniform(2000, 4000)
            change_24h = np.random.uniform(-5, 10)
            rsi = np.random.uniform(30, 80)
            
            if trading_persona == "Degen":
                confluence_score = np.random.randint(70, 95)
                recommendation = "🚀 買進" if confluence_score > 70 else "⏳ 觀望"
            else:
                confluence_score = np.random.randint(50, 75)
                recommendation = "⏳ 觀望" if confluence_score < 70 else "🚀 買進"
            
            st.session_state.analysis_result = {
                "symbol": detected_symbol,
                "price": current_price,
                "change_24h": change_24h,
                "rsi": rsi,
                "confluence_score": confluence_score,
                "recommendation": recommendation,
                "bollinger_enabled": tools_config["bollinger"],
                "ma_enabled": tools_config["ma"],
                "sentiment_enabled": tools_config["sentiment"]
            }
            st.session_state.show_dashboard = True
            st.rerun()
        else:
            ai_response = "⚠️ 請輸入有效的加密貨幣代號（如：BTC、ETH、SOL 等）"
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            st.rerun()
    
    # 顯示儀表板
    if st.session_state.show_dashboard and st.session_state.analysis_result:
        st.divider()
        st.subheader("📊 即時分析儀表板 (Dashboard)")
        
        result = st.session_state.analysis_result
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("當前價格", f"${result['price']:,.2f}", f"{result['change_24h']:+.2f}%")
        col2.metric("RSI 指標", f"{result['rsi']:.1f}")
        col3.metric("共識評分", f"{result['confluence_score']}/100")
        col4.metric("建議動作", result['recommendation'])
        
        st.subheader("📈 互動式 K 線圖")
        dates = pd.date_range(end=datetime.now(), periods=60, freq='h')
        base_price = result['price']
        
        np.random.seed(42)
        opens = base_price + np.random.randn(60).cumsum() * 100
        closes = opens + np.random.randn(60) * 50
        highs = np.maximum(opens, closes) + np.abs(np.random.randn(60) * 30)
        lows = np.minimum(opens, closes) - np.abs(np.random.randn(60) * 30)
        
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
            title=f"{result['symbol']}/USDT",
            yaxis_title="價格 (USD)",
            xaxis_title="時間",
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📝 綜合分析報告")
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown(f"""
### 各項指標貢獻度
            
| 指標 | 評分 | 權重 |
|------|------|------|
| 布林通道 | {np.random.randint(60, 80)}/100 | 30% |
| 移動平均線 | {np.random.randint(70, 90)}/100 | 35% |
| 社群情緒 | {np.random.randint(65, 85)}/100 | 35% |

**最終共識評分**: {result['confluence_score']}/100

**建議動作**: {result['recommendation']}

**理由**: {'社群情緒強勁，價格突破中軌，短線機會明確' if trading_persona == 'Degen' else '趨勢向上但需等待回調，建議觀望或小倉位進場'}

---
*根據 {trading_persona} 交易人格生成*
            """)
        
        with col_right:
            st.info("💡 **操作建議**")
            if "買進" in result['recommendation']:
                st.success(f"✅ 建議買進 {result['symbol']}")
                st.write(f"**建議價格**: ${result['price']:,.2f}")
                st.write("**建議倉位**: 10-20% 資金")
                if st.button("🎯 前往下單", key="go_to_order"):
                    st.success("請切換至「模擬下單」頁籤")
            else:
                st.warning("⏳ 建議觀望")
                st.write("等待更好的進場時機")
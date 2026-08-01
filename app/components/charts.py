# app/components/charts.py
import plotly.graph_objects as go
import pandas as pd

def create_gauge_chart(val, title):
    """建立帶有數值與標題的半圓儀表盤圖表"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",  # 顯示半圓儀表盤 + 中央數字
        value = float(val),
        title = {
            'text': f"<b>{title}</b>", 
            'font': {'size': 16}  # 標題文字大小
        },
        number = {
            'font': {'size': 24, 'weight': 'bold'},  # 中央數字大小
            'valueformat': ".1f"  # 顯示小數點第一位
        },
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#d32f2f", 'thickness': 0.25},  # 🌟 修正：使用 thickness 代替 width
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': '#d9383a'},   # 極度恐懼 / 看空
                {'range': [25, 50], 'color': '#eb8f24'},  # 恐懼
                {'range': [50, 75], 'color': '#f1c40f'},  # 貪婪
                {'range': [75, 100], 'color': '#2ecc71'}  # 極度貪婪 / 看多
            ],
        }
    ))

    # 調整圖表容器邊距與背景，確保文字呈現完整
    fig.update_layout(
        height=190,
        margin=dict(l=25, r=25, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig

def create_candlestick_chart(history_df, symbol, risk_level):
    """創建 K 線與指標疊加圖"""
    history_df['datetime'] = pd.to_datetime(history_df['timestamp'], unit='s')
    
    fig = go.Figure(data=[go.Candlestick(
        x=history_df['datetime'],
        open=history_df['open'], high=history_df['high'],
        low=history_df['low'], close=history_df['close'],
        name=symbol
    )])
    
    # 疊加均線與布林通道
    if 'ma_7' in history_df.columns:
        fig.add_trace(go.Scatter(x=history_df['datetime'], y=history_df['ma_7'], name='MA7', line=dict(color='cyan', width=1)))
    if 'ma_25' in history_df.columns:
        fig.add_trace(go.Scatter(x=history_df['datetime'], y=history_df['ma_25'], name='MA25', line=dict(color='yellow', width=1)))
    if 'bb_upper' in history_df.columns:
        fig.add_trace(go.Scatter(x=history_df['datetime'], y=history_df['bb_upper'], name='布林上軌', line=dict(color='rgba(250, 128, 114, 0.5)', dash='dash')))
        fig.add_trace(go.Scatter(x=history_df['datetime'], y=history_df['bb_lower'], name='布林下軌', line=dict(color='rgba(135, 206, 250, 0.5)', dash='dash')))
        
    fig.update_layout(
        title=f"{symbol}/USDT - 風險等級 {risk_level}",
        yaxis_title="價格 (USD)", xaxis_title="時間",
        template="plotly_dark", height=500,
        xaxis_rangeslider_visible=False
    )
    return fig
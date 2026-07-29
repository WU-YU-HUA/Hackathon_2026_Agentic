# app/components/charts.py
import plotly.graph_objects as go
import pandas as pd

def create_gauge_chart(value, title, color_scheme="fear_greed"):
    """創建半圓儀表盤"""
    colors = ['#d32f2f', '#f57c00', '#ffc107', '#8bc34a', '#4caf50']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': 'white'}},
        number={'font': {'size': 40, 'color': 'white'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white", 'dtick': 25},
            'bar': {'color': "rgba(255, 255, 255, 0.8)", 'thickness': 0.15},
            'bgcolor': "rgba(50, 50, 50, 0.3)",
            'borderwidth': 3,
            'bordercolor': "rgba(255, 255, 255, 0.5)",
            'steps': [
                {'range': [0, 25], 'color': colors[0]},
                {'range': [25, 50], 'color': colors[1]},
                {'range': [50, 75], 'color': colors[2]},
                {'range': [75, 100], 'color': colors[3]},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 6},
                'thickness': 0.85,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin={'t': 40, 'b': 0, 'l': 20, 'r': 20},
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"}
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
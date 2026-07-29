# app/components/onboarding.py
import streamlit as st
import os
import json

def get_allowed_pairs():
    max_pairs_str = os.getenv("MAX_PAIRS", '["BTCUSDT", "ETHUSDT", "SOLUSDT"]')
    try:
        return json.loads(max_pairs_str)
    except:
        return ["BTCUSDT"]

def render_risk_selector():
    """渲染風險評估選擇器"""
    st.subheader("📊 風險評估")
    st.write("請選擇您可接受的風險等級：")
    cols = st.columns(5)
    labels = [("🟢 1", "極低風險"), ("🟡 2", "低風險"), ("🟠 3", "中等風險"), ("🟠 4", "高風險"), ("🔴 5", "極高風險")]
    
    for idx, (icon, text) in enumerate(labels, start=1):
        with cols[idx-1]:
            if st.button(f"{icon}\n{text}", use_container_width=True):
                st.session_state.risk_level = idx
                st.session_state.chat_history.append({"role": "user", "content": f"我選擇風險等級: {idx} ({text})"})
                st.session_state.chat_history.append({"role": "assistant", "content": "了解！接下來請選擇想要分析的交易對。"})
                st.rerun()

def render_pair_selector():
    """渲染交易對選擇器"""
    st.subheader("💱 選擇交易對")
    st.write(f"您的風險等級: **{st.session_state.risk_level}**")
    allowed_pairs = get_allowed_pairs()
    cols = st.columns(min(len(allowed_pairs), 5))
    
    for idx, pair in enumerate(allowed_pairs):
        with cols[idx % 5]:
            symbol = pair.replace("USDT", "").replace("TWD", "")
            if st.button(f"📈 {symbol}", key=f"pair_{pair}", use_container_width=True):
                st.session_state.selected_pair = pair
                st.session_state.current_symbol = symbol
                st.session_state.chat_history.append({"role": "user", "content": f"我想分析 {symbol}"})
                st.session_state.chat_history.append({"role": "assistant", "content": f"好的！正在為您分析 {symbol}，請稍候..."})
                st.rerun()
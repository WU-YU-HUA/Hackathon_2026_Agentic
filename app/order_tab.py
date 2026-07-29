import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import sys
from dotenv import load_dotenv

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.maxAPI import MaxQueryAPI, MaxTradeAPI

# 載入環境變數
load_dotenv()

# 初始化 MAX API
@st.cache_resource
def init_max_api():
    """初始化 MAX API 客戶端"""
    access_key = os.getenv("MAX_ACCESS")
    secret_key = os.getenv("MAX_SECRET")
    
    if not access_key or not secret_key:
        st.error("❌ 未找到 MAX API 金鑰，請檢查 .env 檔案")
        return None, None
    
    query_client = MaxQueryAPI(access_key, secret_key, cache_ttl=60)
    trade_client = MaxTradeAPI(access_key, secret_key)
    
    return query_client, trade_client

def get_allowed_pairs():
    """從 .env 讀取允許的交易對"""
    max_pairs_str = os.getenv("MAX_PAIRS", '["BTCUSDT"]')
    try:
        pairs = json.loads(max_pairs_str)
        return pairs
    except:
        return ["BTCUSDT"]

def parse_symbol_from_pair(pair):
    """從交易對解析出幣種符號 (如 BTCUSDT -> BTC)"""
    return pair.replace("USDT", "").replace("usdt", "")

def render_order_tab():
    """渲染 Tab 2: 真實下單儀表板"""
    st.header("📈 真實下單儀表板")
    
    # 初始化 API 客戶端
    query_client, trade_client = init_max_api()
    
    if not query_client or not trade_client:
        st.error("❌ 無法連接到 MAX API，請檢查配置")
        return
    
    # 獲取允許的交易對
    allowed_pairs = get_allowed_pairs()
    
    # 自動刷新資產資料 (每60秒)
    if 'last_balance_refresh' not in st.session_state:
        st.session_state.last_balance_refresh = 0
    
    current_time = datetime.now().timestamp()
    if current_time - st.session_state.last_balance_refresh >= 60:
        with st.spinner("🔄 更新資產資料中..."):
            try:
                st.session_state.real_balances = query_client.get_all_balance()
                st.session_state.last_balance_refresh = current_time
            except Exception as e:
                st.error(f"❌ 更新資產失敗: {str(e)}")
    
    # 顯示上次更新時間
    if st.session_state.last_balance_refresh > 0:
        time_diff = int(current_time - st.session_state.last_balance_refresh)
        st.caption(f"📊 資產資料已更新 | 上次更新: {time_diff} 秒前 | 自動更新間隔: 60 秒")
    
    # 手動刷新按鈕
    col_refresh, col_space = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 立即刷新", use_container_width=True):
            with st.spinner("🔄 更新資產資料中..."):
                try:
                    st.session_state.real_balances = query_client.get_all_balance()
                    st.session_state.last_balance_refresh = current_time
                    st.success("✅ 資產已更新")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 更新失敗: {str(e)}")
    
    st.divider()
    
    col_form, col_info = st.columns([3, 2])
    
    with col_form:
        st.subheader("📝 下單表單")
        
        # 交易對選擇（只允許 .env 中配置的交易對）
        pair_symbols = [parse_symbol_from_pair(pair) for pair in allowed_pairs]
        
        selected_symbol = st.selectbox(
            "交易幣種",
            pair_symbols,
            help=f"僅支援交易對: {', '.join(allowed_pairs)}"
        )
        
        # 找到對應的完整交易對
        selected_pair = None
        for pair in allowed_pairs:
            if parse_symbol_from_pair(pair) == selected_symbol:
                selected_pair = pair.lower()
                break
        
        if not selected_pair:
            st.error(f"❌ 無法找到 {selected_symbol} 的交易對")
            return
        
        col_side, col_type = st.columns(2)
        with col_side:
            order_side = st.radio("交易方向", ["買進 (Buy)", "賣出 (Sell)"], horizontal=True)
            side_api = "buy" if "買進" in order_side else "sell"
        
        with col_type:
            order_type = st.radio("委託類型", ["市價 (Market)", "限價 (Limit)"], horizontal=True)
        
        # 價格輸入（限價單才需要）
        if "限價" in order_type:
            order_price = st.number_input(
                "委託價格 (USDT)",
                min_value=0.01,
                value=50000.0,
                step=0.01,
                help="限價單必須指定價格"
            )
        else:
            order_price = 0.0
            st.info("💡 市價單將以當前市場最佳價格成交")
        
        # 數量輸入
        if "買進" in order_side:
            # 買入時輸入 USDT 金額
            order_amount_usdt = st.number_input(
                f"買入金額 (USDT)",
                min_value=1.0,
                value=100.0,
                step=10.0,
                format="%.2f",
                help="輸入想要購買的 USDT 金額"
            )
            
            # 估算可購買的幣種數量
            if order_price > 0:
                estimated_amount = order_amount_usdt / order_price
                st.info(f"💡 預估可買入約 {estimated_amount:.6f} {selected_symbol}")
            
            total_value = order_amount_usdt
        else:
            # 賣出時輸入幣種數量
            order_amount = st.number_input(
                f"賣出數量 ({selected_symbol})",
                min_value=0.0001,
                value=0.01,
                step=0.0001,
                format="%.6f",
                help=f"輸入想要賣出的 {selected_symbol} 數量"
            )
            
            if order_price > 0:
                total_value = order_price * order_amount
            else:
                total_value = 0.0
        
        if total_value > 0:
            st.metric("預估金額 (USDT)", f"${total_value:,.2f}")
        
        # 下單按鈕
        col_submit, col_reset = st.columns(2)
        with col_submit:
            if st.button("🚀 確認下單", type="primary", use_container_width=True):
                try:
                    with st.spinner("📡 提交訂單中..."):
                        # 執行下單
                        if "限價" in order_type:
                            # 限價單
                            if "買進" in order_side:
                                quantity = order_amount_usdt / order_price
                            else:
                                quantity = order_amount
                            
                            result = trade_client.limit_order(
                                symbol=selected_pair,
                                side=side_api,
                                price=order_price,
                                quantity=quantity
                            )
                        else:
                            # 市價單
                            if "買進" in order_side:
                                # MAX API 市價買入需要用 USDT 金額
                                quantity = order_amount_usdt
                            else:
                                # 市價賣出用幣種數量
                                quantity = order_amount
                            
                            result = trade_client.market_order(
                                symbol=selected_pair,
                                side=side_api,
                                quantity=quantity
                            )
                        
                        # 檢查回應
                        if 'error' in result:
                            st.error(f"❌ 下單失敗: {result['error']}")
                        elif 'id' in result:
                            st.success(f"✅ 下單成功！")
                            st.json(result)
                            st.balloons()
                            
                            # 刷新餘額
                            st.session_state.real_balances = query_client.get_all_balance()
                            st.session_state.last_balance_refresh = datetime.now().timestamp()
                        else:
                            st.warning("⚠️ 訂單已提交，但回應格式異常")
                            st.json(result)
                        
                except Exception as e:
                    st.error(f"❌ 下單失敗: {str(e)}")
                    st.exception(e)
        
        with col_reset:
            if st.button("🔄 重置表單", use_container_width=True):
                st.rerun()
    
    with col_info:
        st.subheader("📊 帳戶持倉數量")
        
        # 顯示所有資產
        if hasattr(st.session_state, 'real_balances') and st.session_state.real_balances:
            balances = st.session_state.real_balances
            
            # 獨立顯示 USDT 餘額
            usdt_balance = balances.get('usdt', 0.0)
            st.metric("💵 可用 USDT", f"{usdt_balance:,.4f}")
            
            st.divider()
            
            st.write("**📦 各幣種持有數量：**")
            
            # 整理數量大於 0 的幣種成表格顯示
            display_data = []
            for currency, amount in balances.items():
                if currency != 'usdt' and amount > 0:
                    display_data.append({
                        "幣種": currency.upper(),
                        "數量": f"{amount:.6f}"
                    })
            
            if display_data:
                df_balances = pd.DataFrame(display_data)
                # 隱藏 index 並撐滿寬度顯示
                st.dataframe(df_balances, hide_index=True, use_container_width=True)
            else:
                st.info("目前無其他持倉")
                
        else:
            st.info("⏳ 載入資產資料中...")
            # 首次載入
            try:
                st.session_state.real_balances = query_client.get_all_balance()
                st.session_state.last_balance_refresh = datetime.now().timestamp()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 載入失敗: {str(e)}")
    
    st.divider()
    
    # 顯示支援的交易對
    st.subheader("ℹ️ 系統資訊")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"**支援的交易對**: {', '.join(allowed_pairs)}")
    with col_info2:
        st.info(f"**API 狀態**: {'🟢 已連接' if query_client else '🔴 未連接'}")
# 📈 Order Tab 真實下單功能說明

## ✨ 功能特色

### 🔄 自動刷新資產
- 系統每 **60 秒**自動從 MAX API 拉取最新資產資料
- 顯示上次更新時間與倒數計時
- 提供「立即刷新」按鈕手動更新

### 💰 完整資產顯示
- 顯示 **USDT 可用餘額**
- 顯示**所有持倉幣種**及數量
- 自動過濾餘額為 0 的資產

### 🎯 交易對限制
- 僅允許交易 `.env` 中配置的 `MAX_PAIRS`
- 預設支援: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`
- 下拉選單自動過濾，防止誤操作

### 📝 完整下單功能
- **市價單 (Market Order)**
  - 買入: 輸入 USDT 金額
  - 賣出: 輸入幣種數量
- **限價單 (Limit Order)**
  - 指定價格與數量
  - 適合精準進場/出場

---

## 🚀 使用方式

### 1. 配置 .env 檔案
```env
MAX_ACCESS=your_access_key_here
MAX_SECRET=your_secret_key_here
MAX_PAIRS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]
```

### 2. 啟動應用
```powershell
streamlit run app.py
```

### 3. 切換到「模擬下單」頁籤
應用會自動：
- 連接 MAX API
- 載入您的資產
- 開始 60 秒自動刷新計時

---

## 📋 下單流程

### 買入流程
1. 選擇幣種（如 BTC）
2. 選擇「買進 (Buy)」
3. 選擇「市價 (Market)」或「限價 (Limit)」
4. 輸入買入金額（USDT）
   - 市價: 直接以市場價成交
   - 限價: 需指定委託價格
5. 點擊「🚀 確認下單」
6. 系統會：
   - 提交訂單到 MAX
   - 顯示訂單結果
   - 自動刷新餘額

### 賣出流程
1. 選擇幣種（如 BTC）
2. 選擇「賣出 (Sell)」
3. 選擇「市價 (Market)」或「限價 (Limit)」
4. 輸入賣出數量（BTC）
   - 市價: 直接以市場價成交
   - 限價: 需指定委託價格
5. 點擊「🚀 確認下單」
6. 系統會：
   - 提交訂單到 MAX
   - 顯示訂單結果
   - 自動刷新餘額

---

## 🔧 技術實作細節

### API 整合
```python
# 查詢 API - 用於獲取資產
query_client = MaxQueryAPI(access_key, secret_key, cache_ttl=60)
balances = query_client.get_all_balance()

# 交易 API - 用於下單
trade_client = MaxTradeAPI(access_key, secret_key)

# 市價單
result = trade_client.market_order(symbol='btcusdt', side='buy', quantity=100)

# 限價單
result = trade_client.limit_order(symbol='btcusdt', side='sell', price=65000, quantity=0.01)
```

### 自動刷新機制
```python
# 使用 session_state 追蹤上次刷新時間
if current_time - st.session_state.last_balance_refresh >= 60:
    st.session_state.real_balances = query_client.get_all_balance()
    st.session_state.last_balance_refresh = current_time
```

### 交易對解析
```python
# 從 BTCUSDT 解析出 BTC
def parse_symbol_from_pair(pair):
    return pair.replace("USDT", "").replace("usdt", "")
```

---

## ⚠️ 注意事項

### 安全性
- ✅ API Key 儲存在 `.env` 中，不會提交到 Git
- ✅ 使用 `@st.cache_resource` 快取 API 客戶端
- ✅ 交易對白名單機制，防止誤操作

### 資料更新
- 系統會自動每 60 秒更新一次
- 下單後會立即刷新餘額
- 可手動點擊「立即刷新」按鈕

### 限制
- 僅支援 `.env` 中配置的交易對
- 市價買入需輸入 USDT 金額（MAX API 規範）
- 市價賣出需輸入幣種數量

---

## 🐛 疑難排解

### 問題 1: 無法連接到 MAX API
**解決方法**:
1. 檢查 `.env` 中的 `MAX_ACCESS` 和 `MAX_SECRET`
2. 確認 API Key 有效且未過期
3. 檢查網路連線

### 問題 2: 找不到 maxAPI 模組
**解決方法**:
```powershell
# 確認 maxAPI.py 在專案根目錄
ls maxAPI.py

# 檢查 Python 路徑
python -c "import sys; print(sys.path)"
```

### 問題 3: 下單失敗
**可能原因**:
- 餘額不足
- 數量低於最小交易量
- API 限流
- 交易對不存在

**解決方法**:
- 查看錯誤訊息
- 檢查訂單參數
- 確認餘額充足

---

## 📊 功能對照表

| 功能 | 狀態 | 說明 |
|------|------|------|
| 自動刷新資產 | ✅ | 每 60 秒自動更新 |
| 手動刷新按鈕 | ✅ | 立即更新資產 |
| 顯示所有資產 | ✅ | USDT + 所有持倉 |
| 交易對限制 | ✅ | 僅 .env 中配置 |
| 市價買入 | ✅ | 輸入 USDT 金額 |
| 市價賣出 | ✅ | 輸入幣種數量 |
| 限價買入 | ✅ | 指定價格+數量 |
| 限價賣出 | ✅ | 指定價格+數量 |
| 訂單結果顯示 | ✅ | JSON 格式回應 |
| 下單後刷新 | ✅ | 自動更新餘額 |

---

## 🎯 下一步優化建議

1. **訂單歷史查詢**: 整合 MAX API 的訂單查詢功能
2. **掛單管理**: 顯示當前掛單列表與取消功能
3. **價格預警**: 設定目標價格提醒
4. **交易統計**: 顯示今日/本週交易統計
5. **風險控管**: 單筆交易額度限制
6. **即時價格**: 整合 WebSocket 即時價格推送

---

## 📚 相關文件

- `maxAPI.py` - MAX API 封裝
- `order.py` - 下單範例
- `.env` - API 配置檔案
- `md/frontend.md` - 完整規格文檔

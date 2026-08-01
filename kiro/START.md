# 🚀 快速啟動指南

## 📋 前置需求
- Python 3.8+
- 已啟用 conda 環境 `hackathon`

## ⚡ 快速啟動

### 1️⃣ 安裝依賴
```powershell
pip install -r requirements.txt
```

### 2️⃣ 啟動應用
```powershell
streamlit run app.py
```

應用將自動在瀏覽器開啟：`http://localhost:8501`

---

## 📱 功能說明

### Tab 1: 💬 AI Agent 對話與分析
1. 在對話框輸入幣種（如：`分析 BTC`、`ETH 現在能買嗎？`）
2. 系統會自動生成：
   - 📊 數據卡片（價格、RSI、評分、建議）
   - 📈 互動式 K 線圖（含技術指標）
   - 📝 綜合分析報告

### Tab 2: 📈 模擬下單
1. 選擇幣種（會自動帶入 Tab 1 分析的幣種）
2. 選擇買賣方向與委託類型
3. 輸入數量後點擊「確認下單」
4. 查看帳戶餘額、持倉與交易歷史

### 側邊欄: ⚙️ 設定
- **交易人格**：Conservative（穩健）或 Degen（激進）
- **分析工具**：開關布林通道、移動平均線、社群情緒分析
- **帳戶資訊**：即時顯示餘額與持倉

---

## 🎯 使用範例

### 範例 1: 分析 BTC
```
在對話框輸入：幫我分析 BTC
```
系統會顯示完整的 BTC 技術分析儀表板

### 範例 2: 模擬買入
```
1. 切換到「模擬下單」頁籤
2. 選擇 BTC
3. 選擇「買進」、「市價」
4. 輸入數量：0.01
5. 點擊「確認下單」
```

---

## ⚠️ 注意事項
- 本系統目前為**純畫面展示版本**
- 所有數據均為**模擬數據**
- 下單功能僅作**模擬交易**，不會真實扣款
- 實際功能整合請參考 `md/frontend.md`

---

## 🛠️ 疑難排解

### 問題 1: 找不到 streamlit 指令
```powershell
# 確認已安裝
pip list | findstr streamlit

# 重新安裝
pip install streamlit
```

### 問題 2: 畫面無法正常顯示
```powershell
# 清除 Streamlit 快取後重啟
streamlit cache clear
streamlit run app.py
```

### 問題 3: Port 被占用
```powershell
# 使用不同的 port
streamlit run app.py --server.port 8502
```

---

## 📚 相關文件
- `md/frontend.md` - 完整需求規格書
- `readme.md` - 專案總覽
- `requirements.txt` - 依賴清單

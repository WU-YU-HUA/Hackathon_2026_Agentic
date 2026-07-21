# Chainlit 前端介面開發規格書 (Frontend Spec)

## 1. 專案目標
本階段旨在透過 [Chainlit](https://docs.chainlit.io/) 框架，快速建構一個給加密貨幣 AI Agent 使用的互動介面。介面需包含「與 AI 對話分析」以及「觸發模擬下單」兩大核心體驗。

## 2. 介面佈局與核心功能 (UI/UX Requirements)

### 2.1 側邊欄與動態設定 (Sidebar & Settings)
使用 Chainlit 的 `ChatSettings` 讓使用者自訂 AI Agent 的行為：
- **交易人格 (Trading Persona) 下拉選單**：
  - Degen (短線衝鋒：高風險、重視社群情緒)
  - Conservative (穩健長線：低風險、重視大週期 MA)
- **分析工具開關 (Tool Toggles)**：
  - 布林通道 (Bollinger Bands) [預設: ON]
  - 移動平均線 (Moving Averages) [預設: ON]
  - 社群情緒分析 (Social Sentiment) [預設: ON]
> **觸發機制**：當使用者更改設定時 (`@cl.on_settings_update`)，應自動更新系統環境變數或 Agent 的 System Prompt，即時改變其分析邏輯。

### 2.2 主對話視窗 (Chat Interface & Thought Chains)
- 支援使用者輸入加密貨幣代號（如「幫我分析 BTC」或「ETH 現在能買嗎？」）。
- **思考鏈視覺化 (Thought Chains)**：AI 在進行分析時，必須使用 `@cl.step` 裝飾器，讓畫面展開顯示其背景作業。例如：
  - 🔄 `抓取即時價格...`
  - 🔄 `計算布林通道...`
  - 🔄 `分析 Farcaster 社群情緒...`
- **綜合分析報告**：Agent 的最終回覆需使用 Markdown 排版，包含「各項指標貢獻度」與「最終共識評分 (Confluence Score)」。

### 2.3 上下文感知下單 (Context-Aware Ordering via Action/Modal)
取代傳統靜態的「Tab 2」，我們將下單體驗融入對話流中，展現 GenAI 特色：
- **Action Button (行動按鈕)**：當 Agent 判斷給出「買進/賣出」建議時，回覆訊息下方需附帶一個 Chainlit Action Button `[執行下單作業 (Execute Trade)]`。
- **下單表單 (Form/Modal)**：點擊該按鈕後，彈出對話框或新表單（不需讓使用者切換頁面），並**自動填入** Agent 帶入的參數（幣種、建議價格、建議倉位）。
- **確認與回饋**：使用者點擊確認後，畫面上顯示模擬下單成功的提示與交易明細。

## 3. 開發規範
- 請使用 `chainlit` 最新版本開發。
- 將前端邏輯集中於 `app.py`，並預留呼叫後端 API (FastAPI) 或直接呼叫 `tools.py` 內純函數的介面。
- 請勿將複雜的數據計算邏輯寫在前端檔案中。

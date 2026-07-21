# KIRO 開發引導與約束規範 (Steering & Harness)

## 1. 專案背景與架構概念 (Project Identity)
- **專案名稱**：Crypto GenAI Trading Agent (AWS 黑客松專案)
- **技術堆疊**：Python, Chainlit (Frontend UI & Agent Orchestrator), AWS Bedrock (LLM Engine), ccxt/pandas/ta (數據處理)。*(註：FastAPI 僅作為未來跨平台擴充之可選項，目前優先使用記憶體內直接調用)*。
- **核心架構**：無資料庫設計 (Stateless / Cache-based)。資料流向為 **`Chainlit (app.py)` ➔ `Agent Orchestrator (agent.py)` ➔ `純函數工具箱 (tools.py)`**。高度依賴大語言模型的 Tool Calling (Function Calling) 能力來調度指標運算。

## 2. Harness Engineering 約束 (Feedforward Controls)
任何在此專案中生成的程式碼，必須嚴格遵守以下 Harness Engineering 規範：

### 2.1 極致模組化與純函數 (Pure Functions & Modularity)
- **架構職責分離**：
  - `app.py`：僅負責 Chainlit 前端 UI 渲染、Session 狀態管理與使用者互動。
  - `tools.py`：僅存放技術指標計算、下單模擬與外部 API 抓取等純邏輯函數。
  - `agent.py`：負責封裝 System Prompt、管理 LLM 對話歷程與 Tool Calling 調度。
- **純函數要求**：`tools.py` 內的每一個函數 (如 `get_bollinger_bands`, `get_sentiment`) 都必須是**無副作用的 (Side-effect free)**。給定相同的輸入，必須產生相同的輸出。
- **型別與結構化輸出**：
  - 所有 Tool 函數必須包含完整的 Type Hints (`-> dict` 或 Pydantic Model) 與清楚的 Google Style Docstrings，作為 AWS Bedrock Agent 理解工具用途的依據。
  - Tool 回傳的數據除原始數值外，應包含「LLM 易讀特徵」（例如包含 `status: "oversold"` 或 `trend: "bullish"`），以利 Agent 生成精準報告。

### 2.2 錯誤處理與安全邊界 (Safety Sandboxes)
- 不得使用硬編碼 (Hardcoded) 的 API Keys。所有外部密鑰 (X API, Binance API) 必須透過 `python-dotenv` 從 `.env` 檔案中讀取 (`os.getenv`)。
- **Graceful Degradation (優雅降級)**：當第三方 API (例如社群情緒 API) 觸發 Rate Limit 或斷線時，Tool 函數必須捕捉例外 (`try...except`)，並回傳預設的「中性分數 (例如 0.5)」，**絕對不允許讓整個 Agent 崩潰 (Crash)**。

## 3. 反饋循環與測試 (Feedback Sensors)
- 當開發修改 `tools.py` 中的數學計算邏輯時，必須確保與測試檔案 (`tests/test_tools.py`) 同步更新。
- Kiro 在提交程式碼修改前，需自動化檢查是否符合上述型別規範，確認 DataFrame 運算無空值 (NaN) 遺漏錯誤。

## 4. 決策指引 (LLM Context)
這是一份供 KIRO AI Agent (Planner/Coder) 閱讀的規範。當接到使用者的開發指令時：
1. 請嚴格遵守此文件的設計精神，切勿自作主張引入 SQL 資料庫或架設不必要的 FastAPI 路由。
2. 優先確保 `tools.py` 與 `agent.py` 能在記憶體中高效率互相調用。
# `api/__init__.py` Tools 更新說明

本文件記錄 `api/__init__.py` 中 `TOOL_MAP` 與 `TOOLS_SCHEMA` 的更新內容，目的是讓 AI Agent 可呼叫的工具「對標」以下六個資料 / 分析模組，並確保實際可正確執行。

## 更新目標

讓工具完整覆蓋 6 個模組，輸入介面參考各模組 `main()` 的用法：

- `getData` — 技術指標原始數據
- `kline_ai` — 技術面 AI 分析
- `news` — 加密貨幣新聞
- `news_ai` — 新聞面 AI 分析
- `social` — 恐懼貪婪指數 + 多空投票比
- `social_ai` — 情緒面 AI 分析

限制：只更動 `api/__init__.py` 內的工具定義，不修改其他模組的原始程式碼。

## 為什麼需要「包裝層 (Wrapper)」

Agent 呼叫工具時是以 `TOOL_MAP[name](**args)` 的方式把 AI 產生的參數展開帶入函式，因此工具函式的參數必須是「扁平、對 AI 友善」的欄位。但原始模組的簽名並非如此：

1. **簽名不相容**
   - `api.getData.fetch_technical_data(test_name, payload)`
   - `api.social.get_vote_feargreed(test_name, payload)`
   - 兩者都需要 `test_name` 與巢狀的 `payload` dict，無法直接讓 AI 以 `symbol=...` 的方式呼叫。

2. **`_ai` 模組需要串接 (chaining)**
   - `kline_ai` / `news_ai` / `social_ai` 的 `main()` 都是「先抓資料，再把資料丟給 analyzer」兩段式流程，並非單一函式呼叫。

因此在 `api/__init__.py` 內新增薄薄的**包裝函式**：對外提供乾淨的扁平參數介面，對內則依各模組 `main()` 的用法呼叫原始函式（原始碼完全不動）。

## Wrapper 函式與原始模組對應

| 工具名稱 (schema name) | 對標模組 | 內部呼叫流程 |
|---|---|---|
| `get_technical_data` | `getData` | `fetch_technical_data(test_name, payload={"symbol", "boll_window", "boll_dev", "rsi_window"})` |
| `get_kline_ai_analysis` | `kline_ai` | 先 `fetch_technical_data` 取得 `data` → `invoke_kline_analyzer(symbol, kline_data)` |
| `get_crypto_news` | `news` | `fetch_news(tag)` |
| `get_news_ai_analysis` | `news_ai` | 先 `fetch_news(tag)` → `invoke_analyzer(news_data, tag)` |
| `get_vote_feargreed` | `social` | `get_vote_feargreed(test_name, payload={"symbol", "limit"})` |
| `get_social_ai_analysis` | `social_ai` | 先 `get_vote_feargreed` → `invoke_social_analyzer(symbol, fear_and_greed, community_sentiment)` |
| `get_allowed_symbol` | `onboarding` | `get_allowed_pairs()`（沿用既有工具，交易對白名單） |

> 為避免名稱衝突，原始函式以底線別名匯入（例如 `from api.social import get_vote_feargreed as _get_vote_feargreed`），包裝函式再使用對外的公開名稱。

## 工具輸入參數 (TOOLS_SCHEMA)

| 工具 | 參數 | 必填 | 預設 |
|---|---|---|---|
| `get_technical_data` | `symbol` | ✅ | — |
| | `boll_window` | | `20` |
| | `boll_dev` | | `2.0` |
| | `rsi_window` | | `14` |
| `get_kline_ai_analysis` | `symbol` | ✅ | — |
| `get_crypto_news` | `tag` | | `""` |
| `get_news_ai_analysis` | `tag` | ✅ | — |
| `get_vote_feargreed` | `symbol` | | `"BTC"` |
| | `limit` | | `1` |
| `get_social_ai_analysis` | `symbol` | | `"BTC"` |
| | `limit` | | `7` |
| `get_allowed_symbol` | （無參數） | | — |

> 註：舊版 schema 中 `get_technical_data` 曾包含 `interval` 參數，但 `api.getData` 端的 Lambda 會一次回傳全部週期（15m/1h/6h/1d），故已移除該參數以符合實際行為。

## 測試結果（實際呼叫 AWS Lambda）

以 `symbol=BTC` / `tag=BTC` 對七個工具做端到端測試，皆成功回傳有效資料：

| 工具 | 對標模組 | 回傳型別與內容 |
|---|---|---|
| `get_technical_data` | getData | `dict{ metric_type, symbol, data{15m/1h/6h/1d} }` |
| `get_kline_ai_analysis` | kline_ai | `dict{ recommendation, confidence, timeframe_alignment, per_timeframe_analysis, ... }` |
| `get_crypto_news` | news | `list[ {title, context} ]`（30 則） |
| `get_news_ai_analysis` | news_ai | `dict{ overall_sentiment, news_breakdown, key_events, market_impact, ... }` |
| `get_vote_feargreed` | social | `dict{ symbol, fear_and_greed, community_sentiment }` |
| `get_social_ai_analysis` | social_ai | `dict{ recommendation, confidence, sentiment_regime, fng_trend, ... }` |
| `get_allowed_symbol` | onboarding | `list[ "BTCUSDT", "ETHUSDT", ... ]` |

驗證項目：

- `TOOL_MAP` 的 key 與 `TOOLS_SCHEMA` 的 name 完全一致。
- 每個 schema 的 `required` / `properties` 欄位都是對應包裝函式的合法參數。
- 七個工具皆能實際呼叫 AWS Lambda 並取得有效輸出。

> 測試環境備註：在 Windows 主控台（cp950）下，模組內含 emoji 的 `print()` 於 stdout 導向檔案時會出現 `UnicodeEncodeError`；設定 `PYTHONUTF8=1` 後即正常。此為本機終端編碼問題，非工具邏輯錯誤，於 Docker/Linux（UTF-8）環境不受影響。

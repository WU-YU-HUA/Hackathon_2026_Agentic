from api.social import get_vote_feargreed
from api.getData import fetch_technical_data
from app.components.onboarding import get_allowed_pairs
from api.news import fetch_news

TOOL_MAP = {
    "get_vote_feargreed": get_vote_feargreed, #恐懼貪婪指數 + 多空投票比
    "get_technical_data": fetch_technical_data, #技術指標
    "get_allowed_symbol": get_allowed_pairs, #可查詢之交易對
    "get_crypto_news": fetch_news #加密貨幣新聞
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_vote_feargreed",
            "description": "取得加密貨幣市場當前的多空投票比 以及 恐懼貪婪指數(Crypto Fear & Greed Index)。數值為 0~100，0 代表極度恐懼，100 代表極度貪婪。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "欲查詢的天數，預設為 1 (取得最新單日數據)。若使用者想看過去趨勢，可傳入 3 或 7 等數字。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_data",
            "description": "取得指定加密貨幣的最新技術分析數據，包含價格、布林通道(Bollinger Bands)、RSI、MA 與 EMA 等指標。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "加密貨幣交易對名稱，例如 'btcusdt', 'ethusdt', 'xrpusdt'。必須包含 'usdt' 後綴。"
                    },
                    "interval": {
                        "type": "string",
                        "description": "K線週期，支援 '1m','5m','15m','30m','1h','2h','4h','6h','12h','1d'。預設 '1h'。"
                    },
                    "boll_window": {
                        "type": "integer",
                        "description": "布林通道週期視窗，預設 20。"
                    },
                    "boll_dev": {
                        "type": "integer",
                        "description": "布林通道標準差倍數，預設 2。"
                    },
                    "rsi_window": {
                        "type": "integer",
                        "description": "RSI 計算視窗，預設 14。"
                    }
                },
                "required": ["symbol"]  # 強制 AI 必須提供 symbol
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_allowed_symbol",  # 👈 必須與 TOOL_MAP 的 key 完美對應
            "description": "取得系統目前支援/允許分析的加密貨幣交易對清單(白名單)。當使用者詢問「支援哪些幣種」、「可以分析什麼幣」或「有哪些幣可以選」時，呼叫此工具。",
            "parameters": {
                "type": "object",
                "properties": {},  # 👈 因為不需要 AI 傳入參數，所以留空
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_news",
            "description": "從 Cointelegraph 取得最新加密貨幣新聞。可指定主題 (tag) 做來源端搜尋，回傳該主題的相關新聞列表，每則含標題與摘要 (title, context)。當使用者想了解某幣種或市場的最新消息、新聞、動態時呼叫。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "新聞主題標籤。支援幣種代號或交易對 (例如 'bitcoin', 'eth', 'BTCUSDT') 會自動轉換，也支援一般主題 (例如 'regulation', 'defi')。不傳則回傳綜合最新新聞。"
                    }
                },
                "required": []
            }
        }
    }
]
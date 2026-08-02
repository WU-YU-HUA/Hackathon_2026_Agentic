from api.social import get_vote_feargreed as _get_vote_feargreed
from api.getData import fetch_technical_data as _fetch_technical_data
from api.news import fetch_news as _fetch_news
from api.kline_ai import invoke_kline_analyzer as _invoke_kline_analyzer
from api.news_ai import invoke_analyzer as _invoke_news_analyzer
from api.social_ai import invoke_social_analyzer as _invoke_social_analyzer
from app.components.onboarding import get_allowed_pairs


# ==========================================
# 🛠️ 工具包裝層 (Tool Wrappers)
# ==========================================

def get_crypto_news(tag: str = "") -> list | dict:
    """加密貨幣新聞 (news)：呼叫 crypto-news Lambda 取得新聞列表。"""
    try:
        news_data = _fetch_news(tag)
        return news_data if news_data is not None else []
    except Exception as e:
        return {"error": f"無法取得新聞數據: {str(e)}"}


def get_news_ai_analysis(tag: str) -> dict:
    """新聞 AI 分析 (news_ai)：先抓新聞，再交給 crypto-news-ai-analyzer 分析情緒與重點事件。"""
    try:
        news_data = _fetch_news(tag)
        if not news_data:
            return {"error": f"沒有取得與 '{tag}' 相關的新聞資料"}
        # invoke_analyzer 接收 (news_data, tag)
        return _invoke_news_analyzer(news_data, tag)
    except Exception as e:
        return {"error": f"新聞 AI 分析執行失敗: {str(e)}"}


def get_technical_data(symbol: str, boll_window: int = 20, boll_dev: float = 2.0, rsi_window: int = 14) -> dict:
    """技術指標 (getData)：呼叫 crypto-kline Lambda 取得多週期技術數據。"""
    try:
        payload = {
            "symbol": symbol,
            "boll_window": boll_window,
            "boll_dev": boll_dev,
            "rsi_window": rsi_window,
        }
        res = _fetch_technical_data(test_name="get_technical_data", payload=payload)
        if res and isinstance(res, dict) and "data" in res:
            data_dict = res["data"]
            
            # 設定每個時間級別最多保留幾筆 (可依需求調整，建議 50~200)
            MAX_RECORDS = 200 
            
            # 確保 data_dict 是字典格式
            if isinstance(data_dict, dict):
                for interval_key, klines in data_dict.items():
                    # 確保裡面是陣列再進行切片
                    if isinstance(klines, list):
                        # 只保留最後 MAX_RECORDS 筆最新的 K 線
                        data_dict[interval_key] = klines[-MAX_RECORDS:]
                        
        return res if res else {"error": "無法取得技術指標數據"}
    except Exception as e:
        return {"error": f"取得技術數據失敗: {str(e)}"}


def get_kline_ai_analysis(symbol: str) -> dict:
    """K線 AI 分析 (kline_ai)：先抓技術數據，再交給 crypto-kline-ai-analyzer 分析。"""
    try:
        kline_data = _fetch_technical_data(test_name="get_kline_ai_analysis", payload={"symbol": symbol})
        if not kline_data or "data" not in kline_data:
            return {"error": f"無法取得 '{symbol}' 的 K 線數據"}
        
        # 精確取出 payload 中的 data 字典傳入 analyzer
        return _invoke_kline_analyzer(symbol=symbol, kline_data=kline_data.get("data", {}))
    except Exception as e:
        return {"error": f"K線 AI 分析執行失敗: {str(e)}"}


def get_vote_feargreed(symbol: str = "BTC", limit: int = 1) -> dict:
    """恐懼貪婪指數 + 多空投票比 (social)：呼叫 crypto-social Lambda。"""
    try:
        res = _get_vote_feargreed(test_name="get_vote_feargreed", payload={"symbol": symbol, "limit": limit})
        return res if res else {"error": "無法取得社群情緒數據"}
    except Exception as e:
        return {"error": f"取得情緒數據失敗: {str(e)}"}


def get_social_ai_analysis(symbol: str = "BTC", limit: int = 7) -> dict:
    """情緒面 AI 分析 (social_ai)：先抓社群情緒與恐懼貪婪指數，再交給 crypto-social-ai-analyzer 分析。"""
    try:
        social_data = _get_vote_feargreed(test_name="get_social_ai_analysis", payload={"symbol": symbol, "limit": limit})
        if not social_data:
            return {"error": f"無法取得 '{symbol}' 的社群情緒數據"}
        
        fear_and_greed = social_data.get("fear_and_greed", [])
        community_sentiment = social_data.get("community_sentiment", {})
        
        # invoke_social_analyzer 接收 (symbol, fear_and_greed, community_sentiment)
        return _invoke_social_analyzer(
            symbol=symbol,
            fear_and_greed=fear_and_greed,
            community_sentiment=community_sentiment
        )
    except Exception as e:
        return {"error": f"情緒面 AI 分析執行失敗: {str(e)}"}


TOOL_MAP = {
    "get_crypto_news": get_crypto_news,                  # 加密貨幣新聞 (news)
    "get_news_ai_analysis": get_news_ai_analysis,        # 新聞 AI 分析 (news_ai)
    "get_technical_data": get_technical_data,            # 技術指標 (getData)
    "get_kline_ai_analysis": get_kline_ai_analysis,      # K線 AI 分析 (kline_ai)
    "get_vote_feargreed": get_vote_feargreed,            # 恐懼貪婪指數 + 多空投票比 (social)
    "get_social_ai_analysis": get_social_ai_analysis,    # 情緒面 AI 分析 (social_ai)
    "get_allowed_symbol": get_allowed_pairs,             # 可查詢之交易對 (白名單)
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_news",
            "description": "【新聞原始數據】取得加密貨幣新聞列表。注意：此工具會回傳大量原始數據，除非使用者明確要求『列出新聞標題』，否則請優先使用 get_news_ai_analysis。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "新聞主題或幣種代號，例如 'BTC'。若使用者輸入中文請自動轉為標準英文代號。不傳則回傳綜合新聞。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_ai_analysis",
            "description": "【🏆 新聞面首選】針對特定主題的新聞進行 AI 重點摘要、重大事件整理與整體情緒判讀。當使用者詢問『新聞』、『最新消息』、『發生什麼事』或『市場動態』時，【必須優先】呼叫此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "新聞主題或幣種代號，例如 'BTC'、'ETH'。"
                    }
                },
                "required": ["tag"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_data",
            "description": "【⚠️ 警告：回傳數據極大，易導致系統崩潰】取得原始技術指標數據。除非使用者明確要求『我要看具體的 RSI 數值或原始資料』，否則【絕對禁止】呼叫此工具！若要分析趨勢，請務必改用 get_kline_ai_analysis。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "加密貨幣交易對名稱，例如 'BTCUSDT'。"
                    },
                    "boll_window": {
                        "type": "integer",
                        "description": "布林通道週期視窗，預設 20。"
                    },
                    "boll_dev": {
                        "type": "number",
                        "description": "布林通道標準差倍數，預設 2。"
                    },
                    "rsi_window": {
                        "type": "integer",
                        "description": "RSI 計算視窗，預設 14。"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kline_ai_analysis",
            "description": "【🏆 技術面首選】對 K 線與技術指標進行 AI 趨勢分析並給出操作建議。當使用者要求『技術面分析、趨勢判讀、操作策略建議、現在看漲還看跌』時，【必須優先】呼叫此工具，切勿呼叫 get_technical_data！",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "加密貨幣交易對名稱，例如 'BTCUSDT'。"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vote_feargreed",
            "description": "【情緒原始數據】取得市場的恐懼與貪婪指數以及社群多空投票比例。除非使用者單純只想看『指數是多少』，否則分析時請優先使用 get_social_ai_analysis。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "幣種代號，例如 'BTC'。預設 'BTC'。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "欲查詢的天數，預設為 1。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_social_ai_analysis",
            "description": "【🏆 情緒面首選】結合恐懼貪婪指數與社群投票，交由 AI 分析市場當前的極端情緒狀態與操作建議。當需要評估『市場情緒、該恐懼還是貪婪』時請優先呼叫此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "幣種代號，例如 'BTC'。預設 'BTC'。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "納入分析的恐懼貪婪指數天數，預設 7。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_allowed_symbol",
            "description": "【交易對白名單】取得系統目前允許/支援分析的加密貨幣交易對清單。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
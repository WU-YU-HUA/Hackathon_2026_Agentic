import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CoinGecko ID 對應表
# ==========================================
COINGECKO_MAPPING = {
    "btc": "bitcoin",
    "btcusdt": "bitcoin",
    "eth": "ethereum",
    "ethusdt": "ethereum",
    "sol": "solana",
    "solusdt": "solana",
    "doge": "dogecoin",
    "dogeusdt": "dogecoin",
    "xrp": "ripple",
    "xrpusdt": "ripple",
}


class FearGreedData:
    """獲取與處理 Alternative.me 的加密貨幣恐懼與貪婪指數"""

    def __init__(self, limit=1):
        self.limit = limit
        self.api_url = "https://api.alternative.me/fng/"
        self.raw_response = None

    def fetch(self, limit=None):
        if limit is not None:
            self.limit = limit

        try:
            params = {"limit": self.limit}
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            self.raw_response = response.json()
            return True
        except requests.exceptions.RequestException as e:
            print(f"[FearGreedData Error] API 請求失敗: {e}")
            return False

    def get_raw_data(self):
        if not self.raw_response:
            success = self.fetch()
            if not success or not self.raw_response:
                return {"error": "Failed to fetch Fear & Greed data"}

        try:
            data_list = self.raw_response.get("data", [])
            if not data_list:
                return {"error": "No data available in response"}

            if self.limit == 1:
                latest = data_list[0]
                return {
                    "value": int(latest.get("value")),
                    "sentiment": latest.get("value_classification"),
                    "timestamp": int(latest.get("timestamp")),
                    "time_until_update": int(
                        latest.get("time_until_update", 0)
                    ),
                }
            else:
                return [
                    {
                        "value": int(item.get("value")),
                        "sentiment": item.get("value_classification"),
                        "timestamp": int(item.get("timestamp")),
                    }
                    for item in data_list
                ]

        except Exception as e:
            print(f"[FearGreedData Error] 資料解析失敗: {e}")
            return {"error": str(e)}


def fetch_fear_and_greed(limit: int = 1):
    fg = FearGreedData(limit=limit)
    return fg.get_raw_data()


def coinGeckoVote(symbol: str = "btc"):
    """獲取該幣種的多空投票比"""
    query_symbol = symbol.lower().strip()
    cg_id = COINGECKO_MAPPING.get(query_symbol)

    if not cg_id and query_symbol.endswith("usdt"):
        base_symbol = query_symbol.replace("usdt", "")
        cg_id = COINGECKO_MAPPING.get(base_symbol)

    if not cg_id:
        supported_list = ", ".join(sorted(list(set(COINGECKO_MAPPING.values()))))
        return {
            "error": "Symbol mapping not found",
            "message": f"無法取得 '{symbol}' 的社群情緒。目前社群情緒工具僅支援以下幣種：{supported_list}。",
        }

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        up = data.get("sentiment_votes_up_percentage", 0)
        down = data.get("sentiment_votes_down_percentage", 0)

        return {
            "symbol": query_symbol.upper(),
            "coingecko_id": cg_id,
            "up_percentage": up,
            "down_percentage": down,
        }
    except Exception as e:
        return {"error": f"CoinGecko API 請求失敗: {str(e)}"}


def handler(event, context):
    """AWS Lambda 進入點 (同時整合 Fear & Greed 與 CoinGecko 投票)"""
    try:
        params = {}

        if event.get("queryStringParameters"):
            params = event["queryStringParameters"]
        elif event.get("body"):
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
            params = body
        else:
            params = event

        symbol = params.get("symbol", "btc")
        limit = int(params.get("limit", 1))

        # 抓取資料
        fear_greed_res = fetch_fear_and_greed(limit=limit)
        sentiment_vote_res = coinGeckoVote(symbol=symbol)

        result = {
            "symbol": symbol.upper(),
            "fear_and_greed": fear_greed_res,
            "community_sentiment": sentiment_vote_res,
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(result, ensure_ascii=False),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": f"Internal server error: {str(e)}"}, ensure_ascii=False
            ),
        }
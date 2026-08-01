import datetime
import json
import math
import os
import pandas as pd
import requests
from dotenv import load_dotenv
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands

load_dotenv()


def get_allowed_pairs():
    """取得系統允許的交易對白名單"""
    max_pairs_str = os.getenv("MAX_PAIRS", '["BTCUSDT", "ETHUSDT", "SOLUSDT"]')
    try:
        return json.loads(max_pairs_str)
    except Exception:
        return ["BTCUSDT"]


class CryptoData:
    """交易所技術分析工具 (Tool)"""

    def __init__(self, base_url="https://max-api.maicoin.com"):
        self.base_url = base_url

    def get_technical_data(
        self,
        symbol="btcusdt",
        interval="1h",
        period=30,
        boll_window=20,
        boll_dev=2,
        rsi_window=14,
    ):
        symbol = symbol.lower()

        interval_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "6h": 360,
            "12h": 720,
            "1d": 1440,
            "1w": 10080,
        }
        minutes = interval_map.get(interval, 60)

        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=period)
        stime = int(start.timestamp())

        try:
            # 1. 抓取 K 線數據
            path = "/api/v3/k"
            url = self.base_url + path
            params = {
                "market": symbol,
                "period": minutes,
                "timestamp": stime,
                "limit": 10000,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            klines = response.json()

            if not klines:
                return {"error": f"No K-line data returned for {symbol}"}

            # 2. 轉為 DataFrame 並轉型
            df = pd.DataFrame(
                klines,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

            # 3. 計算布林通道
            boll = BollingerBands(
                close=df["close"], window=boll_window, window_dev=boll_dev
            )
            df["bb_middle"] = round(boll.bollinger_mavg(), 5)
            df["bb_upper"] = round(boll.bollinger_hband(), 5)
            df["bb_lower"] = round(boll.bollinger_lband(), 5)

            # 4. 計算 RSI
            rsi = RSIIndicator(close=df["close"], window=rsi_window)
            df["rsi"] = round(rsi.rsi(), 2)

            # 5. 計算 MA (7, 25, 99)
            for p in [7, 25, 99]:
                ma = SMAIndicator(close=df["close"], window=p)
                df[f"ma_{p}"] = round(ma.sma_indicator(), 5)

            # 6. 計算 EMA (7, 25, 99)
            for p in [7, 25, 99]:
                ema = EMAIndicator(close=df["close"], window=p)
                df[f"ema_{p}"] = round(ema.ema_indicator(), 5)

            # 💡 【核心修改區 1】：將整個 DataFrame 轉成 List of Dicts
            records = df.to_dict(orient="records")

            # 💡 【核心修改區 2】：處理前端/JSON 無法解析的 NaN 值 (替換成 None，轉成 JSON 會變 null)
            for record in records:
                for key, val in record.items():
                    if isinstance(val, float) and math.isnan(val):
                        record[key] = None

            timeframe_horizon = "short_term" if minutes < 360 else "long_term"

            # 💡 【核心修改區 3】：回傳整串完整的歷史數據與指標
            return {
                "metric_type": "Technical Analysis Full Series",
                "symbol": symbol.upper(),
                "interval": interval,
                "timeframe_horizon": timeframe_horizon,
                "total_records": len(records),
                "data": records,  # 👈 包含了每一根 K 線的 open/high/low/close/volume + 完整指標
            }

        except Exception as e:
            print(f"[CryptoData Error] 執行失敗: {str(e)}")
            return {"error": str(e)}


def fetch_technical_data(
    symbol: str,
    interval: str = "1h",
    boll_window: int = 20,
    boll_dev: float = 2.0,
    rsi_window: int = 14,
):
    """給 AI / 外部呼叫技術指標的入口"""
    allowed_pairs = [pair.lower() for pair in get_allowed_pairs()]

    query_symbol = symbol.lower()
    if not query_symbol.endswith("usdt"):
        query_symbol += "usdt"

    if query_symbol not in allowed_pairs:
        display_pairs = ", ".join([p.upper() for p in allowed_pairs])
        return {
            "error": "Symbol not allowed",
            "message": f"您查詢的幣種 '{symbol}' 不在系統允許的白名單內。目前系統僅支援：{display_pairs}。",
        }

    crypto_data = CryptoData()
    return crypto_data.get_technical_data(
        symbol=query_symbol,
        interval=interval,
        period=100,
        boll_window=boll_window,
        boll_dev=boll_dev,
        rsi_window=rsi_window,
    )


def handler(event, context):
    """AWS Lambda 進入點 (支援 Direct / API Gateway GET / POST)"""
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

        symbol = params.get("symbol", "btcusdt")
        interval = params.get("interval", "1h")
        boll_window = int(params.get("boll_window", 20))
        boll_dev = float(params.get("boll_dev", 2.0))
        rsi_window = int(params.get("rsi_window", 14))

        result = fetch_technical_data(
            symbol=symbol,
            interval=interval,
            boll_window=boll_window,
            boll_dev=boll_dev,
            rsi_window=rsi_window,
        )

        status_code = 400 if "error" in result else 200

        return {
            "statusCode": status_code,
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
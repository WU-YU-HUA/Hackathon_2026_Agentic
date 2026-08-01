import datetime
import json
import math
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands


def get_allowed_pairs():
    """取得系統允許的交易對白名單"""
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


class CryptoData:
    """交易所技術分析工具 (Tool)"""

    def __init__(self, base_url="https://max-api.maicoin.com"):
        self.base_url = base_url
        # 定義需要抓取的 1m ~ 1d 所有時間週期 (單位：分鐘)
        self.interval_map = {
            "15m": 15,
            "1h": 60,
            "6h": 360,
            "1d": 1440,
        }

    def _fetch_single_interval(
        self,
        symbol,
        minutes,
        period,
        boll_window,
        boll_dev,
        rsi_window,
    ):
        """抓取單一週期的 K 線並計算指標"""
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=period)
        stime = int(start.timestamp())

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
            return []

        df = pd.DataFrame(
            klines,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        numeric_cols = ["open", "high", "low", "close", "volume"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

        # 計算布林通道
        boll = BollingerBands(
            close=df["close"], window=boll_window, window_dev=boll_dev
        )
        df["bb_middle"] = round(boll.bollinger_mavg(), 5)
        df["bb_upper"] = round(boll.bollinger_hband(), 5)
        df["bb_lower"] = round(boll.bollinger_lband(), 5)

        # 計算 RSI
        rsi = RSIIndicator(close=df["close"], window=rsi_window)
        df["rsi"] = round(rsi.rsi(), 2)

        # 計算 MA (7, 25, 99)
        for p in [7, 25, 99]:
            ma = SMAIndicator(close=df["close"], window=p)
            df[f"ma_{p}"] = round(ma.sma_indicator(), 5)

        # 計算 EMA (7, 25, 99)
        for p in [7, 25, 99]:
            ema = EMAIndicator(close=df["close"], window=p)
            df[f"ema_{p}"] = round(ema.ema_indicator(), 5)

        records = df.to_dict(orient="records")

        # 處理 NaN 值 (替換為 None，轉換成 JSON 時會變 null)
        for record in records:
            for key, val in record.items():
                if isinstance(val, float) and math.isnan(val):
                    record[key] = None

        return records

    def get_technical_data(
        self,
        symbol="btcusdt",
        period=30,
        boll_window=20,
        boll_dev=2,
        rsi_window=14,
    ):
        symbol = symbol.lower()
        all_interval_data = {}

        try:
            # 遍歷 1m 到 1d 所有週期
            for interval, minutes in self.interval_map.items():
                interval_key = f"{interval}_data"
                try:
                    records = self._fetch_single_interval(
                        symbol=symbol,
                        minutes=minutes,
                        period=period,
                        boll_window=boll_window,
                        boll_dev=boll_dev,
                        rsi_window=rsi_window,
                    )
                    all_interval_data[interval_key] = records
                except Exception as e:
                    print(f"[CryptoData Warning] 抓取 {interval} 失敗: {str(e)}")
                    all_interval_data[interval_key] = []

            return {
                "metric_type": "Technical Analysis Full Series (All Intervals)",
                "symbol": symbol.upper(),
                "data": all_interval_data,
            }

        except Exception as e:
            print(f"[CryptoData Error] 執行失敗: {str(e)}")
            return {"error": str(e)}


def fetch_technical_data(
    symbol: str,
    boll_window: int = 20,
    boll_dev: float = 2.0,
    rsi_window: int = 14,
):
    """給外部呼叫技術指標的入口"""
    allowed_pairs = [pair.lower() for pair in get_allowed_pairs()]

    query_symbol = symbol.lower()
    if not query_symbol.endswith("usdt"):
        query_symbol += "usdt"

    if query_symbol not in allowed_pairs:
        display_pairs = ", ".join([p.upper() for p in allowed_pairs])
        return {
            "error": "Symbol not allowed",
            "message": f"您查詢的幣種 '{symbol}' 不在系統允許的白名單內。目前僅支援：{display_pairs}。",
        }

    crypto_data = CryptoData()
    return crypto_data.get_technical_data(
        symbol=query_symbol,
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
        boll_window = int(params.get("boll_window", 20))
        boll_dev = float(params.get("boll_dev", 2.0))
        rsi_window = int(params.get("rsi_window", 14))

        result = fetch_technical_data(
            symbol=symbol,
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
import datetime
import pandas as pd
import requests
from dotenv import load_dotenv
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

load_dotenv()


class CryptoData:
    """交易所技術分析工具 (Tool)

    完全彈性設計，支援動態調整 K線週期 (interval)、布林視窗 (boll_window)、
    布林標準差倍數 (boll_dev) 以及 RSI 視窗 (rsi_window)。
    """

    def __init__(self, base_url="https://max-api.maicoin.com"):
        self.base_url = base_url

    def get_technical_data(
        self,
        symbol="btcusdt",
        interval="1h",
        period=30,
        boll_window=20,
        boll_dev=2,  # 👈 新增：布林標準差倍數 (預設為 2)
        rsi_window=14,
    ):
        """抓取指定幣種與時間週期的 K 線，並動態計算布林通道與 RSI 指標。

        :param symbol: 交易對，如 'btcusdt'
        :param interval: K線週期，可選
        '1m','5m','15m','30m','1h','2h','4h','6h','12h','1d','1w'
        :param period: 抓取過去幾天的歷史資料 (預設 30 天，確保資料足夠算指標)
        :param boll_window: 布林通道週期視窗 (預設 20)
        :param boll_dev: 布林通道標準差倍數 (預設 2)
        :param rsi_window: RSI 計算視窗 (預設 14)
        """
        symbol = symbol.lower()

        # 時間週期映射 table (單位：分鐘)
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

        # 計算時間範圍
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

            # 3. 動態計算布林通道 (帶入 boll_window 與 boll_dev)
            boll = BollingerBands(
                close=df["close"], window=boll_window, window_dev=boll_dev
            )
            df["bb_middle"] = round(boll.bollinger_mavg(), 5)
            df["bb_upper"] = round(boll.bollinger_hband(), 5)
            df["bb_lower"] = round(boll.bollinger_lband(), 5)

            # 4. 動態計算 RSI
            rsi = RSIIndicator(close=df["close"], window=rsi_window)
            df["rsi"] = round(rsi.rsi(), 2)

            # 5. 取出最新一筆 K 線數據
            latest = df.iloc[-1]

            # 6. 時間軸屬性標籤 (小於 6 小時算短線，否則算長線)
            timeframe_horizon = "short_term" if minutes < 360 else "long_term"

            return {
                "metric_type": "Technical Analysis",
                "symbol": symbol.upper(),
                "interval": interval,
                "timeframe_horizon": timeframe_horizon,
                "price": latest["close"],
                "bollinger_bands": {
                    "window": boll_window,
                    "dev": boll_dev,  # 回傳當前使用的標準差倍數
                    "upper": latest["bb_upper"],
                    "middle": latest["bb_middle"],
                    "lower": latest["bb_lower"],
                },
                "rsi": {"window": rsi_window, "value": latest["rsi"]},
                "timestamp": int(latest["timestamp"]),
            }

        except Exception as e:
            print(f"[CryptoData Error] 執行失敗: {str(e)}")
            return {"error": str(e)}

    def get_history_df(
        self,
        symbol="btcusdt",
        interval="6h",
        period=12,
        boll_window=20,
        boll_dev=2,
        rsi_window=14,
    ):
        """專門提供給量化策略（如 BollStrategy）使用，回傳包含完整指標的歷史 DataFrame"""
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
        minutes = interval_map.get(interval, 360)

        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=period)
        stime = int(start.timestamp())

        try:
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
                return pd.DataFrame()

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

            return df

        except Exception as e:
            print(f"[CryptoData Error] 取得歷史 DataFrame 失敗: {str(e)}")
            return pd.DataFrame()

# ==========================================
# 獨立測試：模擬 AI Agent 呼叫三次不同設定的場景
# ==========================================
if __name__ == "__main__":
    crypto_tool = CryptoData()

    print("--- 第一次呼叫: 短線 1h (布林 window=20, dev=2) ---")
    res_1h = crypto_tool.get_technical_data(
        symbol="btcusdt", interval="1h", boll_window=20, boll_dev=2
    )
    print(res_1h)

    print("\n--- 第二次呼叫: 長線 6h (布林 window=20, dev=2.5 擴大通道) ---")
    res_6h = crypto_tool.get_technical_data(
        symbol="btcusdt", interval="6h", boll_window=20, boll_dev=2.5
    )
    print(res_6h)

    print("\n--- 第三次呼叫: 長線 1d (主要關注 RSI 14) ---")
    res_1d = crypto_tool.get_technical_data(
        symbol="btcusdt", interval="1d", rsi_window=14
    )
    print(res_1d)
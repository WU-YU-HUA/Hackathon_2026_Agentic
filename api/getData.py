import datetime
import pandas as pd
import requests
from dotenv import load_dotenv
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator, EMAIndicator
from app.components.onboarding import get_allowed_pairs
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

            # 5. 計算 MA (Simple Moving Average) - 7, 25, 99
            ma_periods = [7, 25, 99]
            for period in ma_periods:
                ma = SMAIndicator(close=df["close"], window=period)
                df[f"ma_{period}"] = round(ma.sma_indicator(), 5)

            # 6. 計算 EMA (Exponential Moving Average) - 7, 25, 99
            ema_periods = [7, 25, 99]
            for period in ema_periods:
                ema = EMAIndicator(close=df["close"], window=period)
                df[f"ema_{period}"] = round(ema.ema_indicator(), 5)

            # 7. 取出最新一筆 K 線數據
            latest = df.iloc[-1]

            # 8. 時間軸屬性標籤 (小於 6 小時算短線，否則算長線)
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
                "ma": {
                    "ma_7": latest["ma_7"],
                    "ma_25": latest["ma_25"],
                    "ma_99": latest["ma_99"],
                },
                "ema": {
                    "ema_7": latest["ema_7"],
                    "ema_25": latest["ema_25"],
                    "ema_99": latest["ema_99"],
                },
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

            # 計算 MA (Simple Moving Average) - 7, 25, 99
            ma_periods = [7, 25, 99]
            for period in ma_periods:
                ma = SMAIndicator(close=df["close"], window=period)
                df[f"ma_{period}"] = round(ma.sma_indicator(), 5)

            # 計算 EMA (Exponential Moving Average) - 7, 25, 99
            ema_periods = [7, 25, 99]
            for period in ema_periods:
                ema = EMAIndicator(close=df["close"], window=period)
                df[f"ema_{period}"] = round(ema.ema_indicator(), 5)

            return df

        except Exception as e:
            print(f"[CryptoData Error] 取得歷史 DataFrame 失敗: {str(e)}")
            return pd.DataFrame()

def fetch_technical_data(
    symbol: str, 
    interval: str = "1h", 
    boll_window: int = 20, 
    boll_dev: int = 2, 
    rsi_window: int = 14):
    """給 AI 呼叫技術指標的入口 (包含防呆限制)"""
    
    # 1. 取得允許的交易對清單，並【強制轉小寫】確保比對不會出錯
    allowed_pairs = [pair.lower() for pair in get_allowed_pairs()]
    
    # 2. 格式化 AI 傳入的 symbol (防呆：如果 AI 只傳 'btc'，自動補上 'usdt')
    query_symbol = symbol.lower()
    if not query_symbol.endswith("usdt"):
        query_symbol += "usdt"
        
    # 3. 檢查是否在允許清單內
    if query_symbol not in allowed_pairs:
        # 把清單轉回大寫顯示給 AI，讓 AI 回答給使用者時比較好看
        display_pairs = ", ".join([p.upper() for p in allowed_pairs])
        return {
            "error": "Symbol not allowed",
            "message": f"您查詢的幣種 '{symbol}' 不在系統允許的白名單內。目前系統僅支援分析以下交易對：{display_pairs}。請依照此清單重新回答使用者。"
        }

    # 4. 通過檢查，執行真正的資料抓取
    crypto_data = CryptoData()
    return crypto_data.get_technical_data(
        symbol=query_symbol,
        interval=interval,
        period=100,
        boll_window=boll_window,
        boll_dev=boll_dev,
        rsi_window=rsi_window
    )
# ==========================================
# 獨立測試：模擬 AI Agent 呼叫三次不同設定的場景
# ==========================================
if __name__ == "__main__":
    crypto_tool = CryptoData()

    print("=" * 80)
    print("--- 第一次呼叫: 短線 1h (布林 window=20, dev=2) ---")
    print("=" * 80)
    res_1h = crypto_tool.get_technical_data(
        symbol="btcusdt", interval="1h", boll_window=20, boll_dev=2
    )
    print(f"Symbol: {res_1h.get('symbol')}")
    print(f"Price: {res_1h.get('price')}")
    print(f"RSI: {res_1h.get('rsi')}")
    print(f"MA: {res_1h.get('ma')}")
    print(f"EMA: {res_1h.get('ema')}")
    print(f"Bollinger Bands: {res_1h.get('bollinger_bands')}")

    print("\n" + "=" * 80)
    print("--- 第二次呼叫: 長線 6h (布林 window=20, dev=2.5 擴大通道) ---")
    print("=" * 80)
    res_6h = crypto_tool.get_technical_data(
        symbol="btcusdt", interval="6h", boll_window=20, boll_dev=2.5
    )
    print(f"Symbol: {res_6h.get('symbol')}")
    print(f"Price: {res_6h.get('price')}")
    print(f"RSI: {res_6h.get('rsi')}")
    print(f"MA: {res_6h.get('ma')}")
    print(f"EMA: {res_6h.get('ema')}")
    print(f"Bollinger Bands: {res_6h.get('bollinger_bands')}")

    print("\n" + "=" * 80)
    print("--- 第三次呼叫: 長線 1d (主要關注 RSI 14) ---")
    print("=" * 80)
    res_1d = crypto_tool.get_technical_data(
        symbol="btcusdt", interval="1d", rsi_window=14
    )
    print(f"Symbol: {res_1d.get('symbol')}")
    print(f"Price: {res_1d.get('price')}")
    print(f"RSI: {res_1d.get('rsi')}")
    print(f"MA: {res_1d.get('ma')}")
    print(f"EMA: {res_1d.get('ema')}")
    print(f"Bollinger Bands: {res_1d.get('bollinger_bands')}")
    
    print("\n" + "=" * 80)
    print("--- 測試完畢：成功計算 MA (7, 25, 99) 和 EMA (7, 25, 99) ---")
    print("=" * 80)
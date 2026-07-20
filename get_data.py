import requests
import pandas as pd
import datetime
from ta.volatility import BollingerBands

class CryptoData:
    def __init__(self, symbol="btcusdt", interval="1h", period=20, end=None):
        if end is None:
            end = datetime.datetime.now()
            
        # MAX 交易所的交易對皆為小寫 (例如: btcusdt)
        self.symbol = symbol.lower()
        
        # 將幣安的字串格式轉換為 MAX 需要的分鐘數 (MAX: 1, 5, 15, 30, 60, 120, 240, 360, 720, 1440, 4320, 10080)
        interval_map = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "6h": 360, "12h": 720,
            "1d": 1440, "1w": 10080
        }
        self.interval = interval_map.get(interval, 60) # 預設為 60 分鐘 (1小時)
        
        # 修正了原本的拼字錯誤 (kline_date -> kline_data)
        self.kline_data = pd.DataFrame() 
        self.start = end - datetime.timedelta(days=period)
        self.end = end
        
        # MAX API Base URL
        self.base_url = "https://max-api.maicoin.com"

    def get_kline_data(self):
        try:
            # MAX 交易所的 timestamp 是以「秒」為單位 (幣安是毫秒)
            stime = int(self.start.timestamp())
            
            path = "/api/v3/klines"
            url = self.base_url + path
            
            # 設定 API 請求參數
            params = {
                'market': self.symbol,
                'period': self.interval,
                'timestamp': stime,
                'limit': 10000 # 確保拿取足夠的資料量 (MAX 預設 30，最大 10000)
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status() # 如果發生 HTTP 錯誤會拋出異常
            klines = response.json()
            
            # MAX K線回傳格式: [ [timestamp, open, high, low, close, volume], ... ]
            self.kline_data = pd.DataFrame(klines, columns=[
                "timestamp", "open", "high", "low", "close", "volume"
            ])
            
            # ta 套件計算時需要確保資料型態為數值 (float)
            numeric_cols = ["open", "high", "low", "close", "volume"]
            self.kline_data[numeric_cols] = self.kline_data[numeric_cols].apply(pd.to_numeric)
            
        except Exception as e:
            print(f"Wrong get data -- {str(e)}")
    
    def cal_boll(self, window=20, dev=2):
        try:
            self.get_kline_data()
            
            # 確保資料有成功抓下來
            if self.kline_data.empty:
                print("No data available to calculate Bollinger Bands.")
                return

            boll_indicator = BollingerBands(close=self.kline_data['close'], window=window, window_dev=dev)

            self.kline_data["bb_middle"] = round(boll_indicator.bollinger_mavg(), 5)   # 中軌
            self.kline_data["bb_upper"]  = round(boll_indicator.bollinger_hband(), 5)  # 上軌
            self.kline_data["bb_lower"]  = round(boll_indicator.bollinger_lband(), 5)  # 下軌
            
        except Exception as e:
            print(f"Wrong calculate -- {str(e)}")


# ==========================================
# 測試執行區塊
# ==========================================
if __name__ == '__main__':
    # 抓取 MAX 交易所 btcusdt 的 1小時 K線，回推 20 天
    crypto = CryptoData(symbol="btcusdt", interval="1h", period=20)
    crypto.cal_boll()
    
    # 印出最後 5 筆資料來檢查布林通道有沒有算出來
    print(crypto.kline_data.tail())
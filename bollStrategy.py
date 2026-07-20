from getData import CryptoData
from order import orderAPI

###### Bolling *3

class BollStrategy:
    def __init__(self, symbol, key, secret, narrow, slop, windows, dev):
        self.symbol = symbol
        self.data = CryptoData(symbol=self.symbol, interval="6h", period=12) #回測發現6h的Bolling通道最好
        self.binance = orderAPI(key=key, secret=secret)
        self.narrow = narrow
        self.slop = slop
        self.windows = windows
        self.dev = dev

        self.order_exist = False
        self.quantity = 0
        self.open_time = None
        self.money = 0
        self.end_time = None
        
        # 新增一個變數，用來儲存偵錯訊息
        self.debug_msg = ""

    def detect_in(self, data=None): #判斷入場點 2:現在 0,1:前根
        try:
            if data:
                data = data
            else:
                self.data.cal_boll(window=self.windows, dev=self.dev)
                data = self.data.kline_date.to_dict(orient='records')[-3:]

            narrow = (data[0].get('bb_upper') - data[0].get('bb_lower'))/data[0].get('bb_middle')
            narrow2 = (data[1].get('bb_upper') - data[1].get('bb_lower'))/data[1].get('bb_middle')
            slop = data[1].get('bb_middle')/data[0].get('bb_middle') - 1

            high_price = float(data[1].get('high'))
            upper_band = float(data[1].get('bb_upper'))

            # 將判斷拆解，方便紀錄
            cond1 = narrow2 > narrow
            cond2 = narrow < self.narrow
            cond3 = slop > self.slop
            cond4 = high_price >= upper_band

            # 組合你要看的偵錯文字
            self.debug_msg = (
                f"🔎 [進場檢查]\n"
                f"  - 窄度: {narrow:.4f} (需 < {self.narrow}: {'✅' if cond2 else '❌'})\n"
                f"  - 斜率: {slop:.5f} (需 > {self.slop}: {'✅' if cond3 else '❌'})\n"
                f"  - 價格: {high_price} (需 >= 上軌 {upper_band:.2f}: {'✅' if cond4 else '❌'})"
            )

            return cond1 and cond2 and cond3 and cond4 
        except Exception as e:
            self.debug_msg = f"❌ 進場判斷發生錯誤: {str(e)}"
            return False

    def detect_out(self, data=None): #判斷出場點*4  3:現在 0,1,2:前根
        try:
            if data:
                data = data
            else:
                self.data.cal_boll(window=self.windows, dev=self.dev)
                data = self.data.kline_date.to_dict(orient='records')[-4:]
            
            if self.open_time == data[3].get('open_time'):
                self.debug_msg = "⏳ [出場檢查] K線尚未換根，不執行出場判定。"
                return False
                
            slop = data[1].get('bb_middle')/data[0].get('bb_middle') - 1
            slop2 = data[2].get('bb_middle')/data[1].get('bb_middle') - 1
            
            close_price = float(data[2].get('close'))
            mid_band = float(data[2].get('bb_middle'))
            prev_low = float(data[1].get('low'))
            prev_mid = float(data[1].get('bb_middle'))

            cond1 = slop2 < self.slop
            cond2 = slop2 < slop
            cond3 = (close_price <= mid_band * 0.99) or (prev_low <= prev_mid)

            self.debug_msg = (
                f"🔎 [出場檢查]\n"
                f"  - 斜率下降: {'✅' if cond2 else '❌'}\n"
                f"  - 斜率過低: {slop2:.5f} (需 < {self.slop}: {'✅' if cond1 else '❌'})\n"
                f"  - 跌破中軌: {'✅' if cond3 else '❌'}"
            )
            
            return cond1 and cond2 and cond3
            
        except Exception as e:
            self.debug_msg = f"❌ 出場判斷發生錯誤: {str(e)}"
            return False

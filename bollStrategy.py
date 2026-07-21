from getData import CryptoData

###### Bolling *3

class BollStrategy:
    def __init__(self, symbol, narrow, slop, windows, dev):
        self.symbol = symbol
        self.data = CryptoData(symbol=self.symbol, interval="6h", period=12) #回測發現6h的Bolling通道最好
        
        self.narrow = narrow
        self.slop = slop
        self.windows = windows
        self.dev = dev
        
        # 僅保留 debug_msg 用於傳遞判斷過程的文字
        self.debug_msg = ""

    def get_market_advice(self):
        """
        同時判斷「假設未入場」與「假設已入場」的情況，
        並產生一份適合給前端 (Chainlit) 顯示的綜合分析報告。
        """
        # 1. 統一計算一次布林通道，避免 in/out 重複發送 API 請求
        self.data.cal_boll(window=self.windows, dev=self.dev)
        
        # 確保資料足夠判斷 (至少需要 4 根 K 線)
        if self.data.kline_data.empty or len(self.data.kline_data) < 4:
            return "⚠️ 資料不足，無法進行布林通道分析。"
            
        # 2. 將資料轉為字典，並切片準備給 detect_in 與 detect_out 使用
        records = self.data.kline_data.to_dict(orient='records')
        data_in = records[-3:]
        data_out = records[-4:]

        # 3. 假設未入場：判斷是否該進場
        suggest_enter = self.detect_in(data=data_in)
        msg_in = self.debug_msg

        # 4. 假設已入場：判斷是否該出場
        suggest_exit = self.detect_out(data=data_out)
        msg_out = self.debug_msg

        # 5. 組合最終的分析報告 (Markdown 格式，適合 Chainlit)
        advice = "📊 **【市場盤勢分析報告】**\n\n"
        
        advice += "🟢 **【假設尚未入場】**\n"
        advice += msg_in + "\n"
        advice += f"👉 **結論：{'建議立刻進場買入 🚀' if suggest_enter else '條件未滿足，建議觀望 ⏳'}**\n\n"
        
        advice += "🔴 **【假設已持有部位】**\n"
        advice += msg_out + "\n"
        advice += f"👉 **結論：{'建議立刻平倉出場 🛑' if suggest_exit else '趨勢延續中，建議繼續持有 💎'}**\n"

        # 回傳綜合文字報告，以及布林值方便主程式寫邏輯
        return {
            "suggest_enter": suggest_enter,
            "suggest_exit": suggest_exit,
            "report_text": advice
        }

    def detect_in(self, data=None): #判斷入場點 2:現在 0,1:前根
        try:
            if data:
                data = data
            else:
                self.data.cal_boll(window=self.windows, dev=self.dev)
                data = self.data.kline_data.to_dict(orient='records')[-3:]

            narrow = (data[0].get('bb_upper') - data[0].get('bb_lower'))/data[0].get('bb_middle')
            narrow2 = (data[1].get('bb_upper') - data[1].get('bb_lower'))/data[1].get('bb_middle')
            slop = data[1].get('bb_middle')/data[0].get('bb_middle') - 1

            high_price = float(data[1].get('high'))
            upper_band = float(data[1].get('bb_upper'))

            cond1 = narrow2 > narrow
            cond2 = narrow < self.narrow
            cond3 = slop > self.slop
            cond4 = high_price >= upper_band

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
                data = self.data.kline_data.to_dict(orient='records')[-4:]
            
            # (移除狀態相關的 open_time 檢查，純看 K 線數據)
                
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
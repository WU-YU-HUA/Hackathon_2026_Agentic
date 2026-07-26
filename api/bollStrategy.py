from getData import CryptoData


class BollStrategy:

    def __init__(self, symbol, narrow, slop, windows, dev, interval="6h"):
        self.symbol = symbol
        self.narrow = narrow
        self.slop = slop
        self.windows = windows  # 對應 boll_window
        self.dev = dev  # 對應 boll_dev
        self.interval = interval

        # 初始化新版的 CryptoData 工具
        self.crypto_tool = CryptoData()
        self.debug_msg = ""

    def get_market_advice(self):
        """同時判斷「假設未入場」與「假設已入場」的情況，並產生綜合分析報告。"""
        # 1. 向新版 CryptoData 取得計算好的歷史 DataFrame (固定推 12 天確保數據足夠)
        df = self.crypto_tool.get_history_df(
            symbol=self.symbol,
            interval=self.interval,
            period=12,
            boll_window=self.windows,
            boll_dev=self.dev,
        )

        # 確保資料足夠判斷 (至少需要 4 根 K 線)
        if df.empty or len(df) < 4:
            return "⚠️ 資料不足，無法進行布林通道分析。"

        # 2. 將資料轉為字典，切片準備給 detect_in 與 detect_out 使用
        records = df.to_dict(orient="records")
        data_in = records[-3:]
        data_out = records[-4:]

        # 3. 假設未入場：判斷是否該進場
        suggest_enter = self.detect_in(data=data_in)
        msg_in = self.debug_msg

        # 4. 假設已入場：判斷是否該出場
        suggest_exit = self.detect_out(data=data_out)
        msg_out = self.debug_msg

        # 5. 組合最終的 Markdown 分析報告
        advice = "📊 **【市場盤勢分析報告】**\n\n"

        advice += "🟢 **【假設尚未入場】**\n"
        advice += msg_in + "\n"
        advice += f"👉 **結論：{'建議立刻進場買入 🚀' if suggest_enter else '條件未滿足，建議觀望 ⏳'}**\n\n"

        advice += "🔴 **【假設已持有部位】**\n"
        advice += msg_out + "\n"
        advice += f"👉 **結論：{'建議立刻平倉出場 🛑' if suggest_exit else '趨勢延續中，建議繼續持有 💎'}**\n"

        return {
            "suggest_enter": suggest_enter,
            "suggest_exit": suggest_exit,
            "report_text": advice,
        }

    def detect_in(self, data=None):
        """判斷入場點"""
        try:
            if not data:
                df = self.crypto_tool.get_history_df(
                    symbol=self.symbol,
                    interval=self.interval,
                    period=12,
                    boll_window=self.windows,
                    boll_dev=self.dev,
                )
                data = df.to_dict(orient="records")[-3:]

            narrow = (data[0].get("bb_upper") - data[0].get("bb_lower")) / data[
                0
            ].get("bb_middle")
            narrow2 = (
                data[1].get("bb_upper") - data[1].get("bb_lower")
            ) / data[1].get("bb_middle")
            slop = data[1].get("bb_middle") / data[0].get("bb_middle") - 1

            high_price = float(data[1].get("high"))
            upper_band = float(data[1].get("bb_upper"))

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

    def detect_out(self, data=None):
        """判斷出場點"""
        try:
            if not data:
                df = self.crypto_tool.get_history_df(
                    symbol=self.symbol,
                    interval=self.interval,
                    period=12,
                    boll_window=self.windows,
                    boll_dev=self.dev,
                )
                data = df.to_dict(orient="records")[-4:]

            slop = data[1].get("bb_middle") / data[0].get("bb_middle") - 1
            slop2 = data[2].get("bb_middle") / data[1].get("bb_middle") - 1

            close_price = float(data[2].get("close"))
            mid_band = float(data[2].get("bb_middle"))
            prev_low = float(data[1].get("low"))
            prev_mid = float(data[1].get("bb_middle"))

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


# ==========================================
# 獨立測試執行區塊
# ==========================================
if __name__ == "__main__":
    # 初始化策略 (帶入你的布林參數)
    strategy = BollStrategy(
        symbol="ethusdt", narrow=0.06, slop=0.001, windows=25, dev=2.2
    )
    result = strategy.get_market_advice()

    if isinstance(result, dict):
        print(result["report_text"])
    else:
        print(result)
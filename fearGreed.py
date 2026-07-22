import requests


class FearGreedData:
    """獲取與處理 Alternative.me 的加密貨幣恐懼與貪婪指數 (Crypto Fear & Greed Index)

    設計為純粹的 Tool/Data 模組，方便未來直接提供給 AI Agent 作為 Context。
    """

    def __init__(self, limit=1):
        """:param limit: 抓取天數，預設為 1 (最新一天)"""
        self.limit = limit
        self.api_url = "https://api.alternative.me/fng/"
        self.raw_response = None

    def fetch(self, limit=None):
        """從 Alternative.me API 抓取原始資料"""
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
        """解析並回傳結構化的數據字典。

        若 limit=1，回傳單一字典；若 limit > 1，回傳字典列表。 適合直接提供給 LLM 進行分析。
        """
        # 若尚未抓取資料，則自動執行一次 fetch
        if not self.raw_response:
            success = self.fetch()
            if not success or not self.raw_response:
                return {"error": "Failed to fetch Fear & Greed data"}

        try:
            data_list = self.raw_response.get("data", [])
            if not data_list:
                return {"error": "No data available in response"}

            # 若 limit = 1，回傳單一最即時的數據字典
            if self.limit == 1:
                latest = data_list[0]
                return {
                    "value": int(latest.get("value")),
                    "sentiment": latest.get("value_classification"),
                    "timestamp": latest.get("timestamp"),
                    "time_until_update": latest.get("time_until_update"),
                }
            # 若 limit > 1，回傳多天歷史數據陣列
            else:
                return [
                    {
                        "value": int(item.get("value")),
                        "sentiment": item.get("value_classification"),
                        "timestamp": item.get("timestamp"),
                    }
                    for item in data_list
                ]

        except Exception as e:
            print(f"[FearGreedData Error] 資料解析失敗: {e}")
            return {"error": str(e)}


# ==========================================
# 獨立測試執行區塊
# ==========================================
if __name__ == "__main__":
    print("=== 測試 1: 抓取最新單天數據 ===")
    fg = FearGreedData(limit=1)
    data = fg.get_raw_data()
    print(data)

    print("\n=== 測試 2: 抓取歷史 3 天數據 ===")
    fg_history = FearGreedData(limit=3)
    history_data = fg_history.get_raw_data()
    print(history_data)
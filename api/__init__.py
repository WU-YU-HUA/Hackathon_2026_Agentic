from .fearGreed import fetch_fear_and_greed

TOOL_MAP = {
    "get_fear_and_greed": fetch_fear_and_greed
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_fear_and_greed",
            "description": "取得加密貨幣市場當前的恐懼貪婪指數(Crypto Fear & Greed Index)。數值為 0~100，0 代表極度恐懼，100 代表極度貪婪。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "欲查詢的天數，預設為 1 (取得最新單日數據)。若使用者想看過去趨勢，可傳入 3 或 7 等數字。"
                    }
                },
                "required": []
            }
        }
    }
]
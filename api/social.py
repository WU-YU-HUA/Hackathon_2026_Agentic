import json
import requests

import requests

# ==========================================
# CoinGecko ID 對應表
# ==========================================
COINGECKO_MAPPING = {
    "btc": "bitcoin",
    "btcusdt": "bitcoin",
    "eth": "ethereum",
    "ethusdt": "ethereum",
    "sol": "solana",
    "solusdt": "solana",
    "doge": "dogecoin",
    "dogeusdt": "dogecoin",
    "xrp": "ripple",
    "xrpusdt": "ripple"
    # 若未來有新增幣種，直接加在這裡即可
}

def coinGeckoVote(symbol: str = "btc"):
    """獲取該幣種的多空投票比，自動處理 symbol 到 CoinGecko ID 的轉換"""
    
    # 1. 轉小寫與清理
    query_symbol = symbol.lower().strip()
    
    # 2. 嘗試從 Mapping 表找出對應的 CoinGecko ID
    cg_id = COINGECKO_MAPPING.get(query_symbol)
    
    # 防呆：如果 AI 傳了帶有 usdt 的字串但 mapping 沒寫好，嘗試拔掉 usdt 再對應一次
    if not cg_id and query_symbol.endswith("usdt"):
        base_symbol = query_symbol.replace("usdt", "")
        cg_id = COINGECKO_MAPPING.get(base_symbol)

    # 3. 如果真的找不到，回傳友善錯誤訊息教導 AI
    if not cg_id:
        supported_list = ", ".join(set(COINGECKO_MAPPING.values()))
        return {
            "error": "Symbol mapping not found",
            "message": f"無法取得 '{symbol}' 的社群情緒。目前社群情緒工具僅支援以下幣種：{supported_list}。請告知使用者暫不支援該幣種。"
        }

    # 4. 成功找到 ID，呼叫真正的 API
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 檢查 HTTP 狀態碼
        data = response.json()
        
        up = data.get("sentiment_votes_up_percentage", 0)
        down = data.get("sentiment_votes_down_percentage", 0)
        
        return {
            "symbol": query_symbol.upper(),
            "coingecko_id": cg_id,
            "up_percentage": up,
            "down_percentage": down
        }
    except Exception as e:
        return {"error": f"CoinGecko API 請求失敗: {str(e)}"}



if __name__ == "__main__":
    vote = coinGeckoVote("btc")
    print(vote)
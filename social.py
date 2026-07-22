import json
import requests

def save_response(response):
    """將 API 回應存成 JSON 檔案"""
    with open("response.json", 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False, indent=4)

def coinGeckoVote(symbol:str = "bitcoin"):
    """獲取該幣種的多空投票比，需要先查詢幣種的英文id"""
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}"

    response = requests.get(url)
    data = response.json()
    up = data.get("sentiment_votes_up_percentage", 0)
    down = data.get("sentiment_votes_down_percentage", 0)
    return {"up": up, "down": down}



if __name__ == "__main__":
    pass
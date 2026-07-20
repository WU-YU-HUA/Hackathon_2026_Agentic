import os
from dotenv import load_dotenv
from maxAPI import MaxQueryAPI, MaxTradeAPI
load_dotenv()

# 假設你為了安全，申請了兩組不同的 Key
ACCESS_KEY = os.getenv("MAX_ACCESS")
SECRET_KEY = os.getenv("MAX_SECRET")

# 給前端 UI 顯示餘額用的實例
query_client = MaxQueryAPI(ACCESS_KEY, SECRET_KEY)
print(f"目前 USDT 餘額: {query_client.get_money('usdt')}")

# 給後端策略觸發下單用的實例
trade_client = MaxTradeAPI(ACCESS_KEY, SECRET_KEY)
# trade_client.market_order('btcusdt', 'buy', 0.01)
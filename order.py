from binance.um_futures import UMFutures

class orderAPI:
    def __init__(self, key, secret):
        self.api_key = key
        self.api_secret = secret
        self.client = UMFutures(key=self.api_key, secret=self.api_secret)

    def get_money(self):
        account_info = self.client.account()
        assets = account_info.get('assets')
        usdt = next((asset for asset in assets if asset.get('asset') == "USDT"), None)
        balance = usdt.get('marginBalance')

        return balance

    def market_order(self, symbol, side, quantity):
        order = self.client.new_order(
            symbol=symbol,
            side=side,          # BUY or SELL
            type="MARKET",       # 市價單
            quantity=quantity    # SUI 顆數
        )

    def get_position(self, symbol=None):
        account_info = self.client.account()
        positions = account_info.get('positions') # 因為只有一種幣別，一個方向
        amount = None
        
        for position in positions:
            if position.get('symbol') == symbol:
                amount = position.get('positionAmt')

        return amount

if __name__ == "__main__":
    pass

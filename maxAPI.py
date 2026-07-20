import time
import json
import hmac
import hashlib
import base64
import requests

# 1. 核心基底：只負責身分驗證與發送請求
class MaxBaseAPI:
    def __init__(self, key, secret):
        self.api_key = key
        self.api_secret = secret
        self.base_url = "https://max-api.maicoin.com"

    def _send_request(self, method, path, params=None):
        if params is None:
            params = {}
        
        params['nonce'] = int(time.time() * 1000)
        params_to_be_signed = params.copy()
        params_to_be_signed['path'] = path

        json_str = json.dumps(params_to_be_signed, separators=(',', ':'))
        payload = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'X-MAX-ACCESSKEY': self.api_key,
            'X-MAX-PAYLOAD': payload,
            'X-MAX-SIGNATURE': signature,
            'Content-Type': 'application/json',
        }

        url = self.base_url + path
        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.request(method, url, json=params, headers=headers)
            
        return response.json()


# 2. 查詢模組：繼承 Base，專門放 GET 類型的唯讀操作
class MaxQueryAPI(MaxBaseAPI):
    def get_money(self, asset="usdt"):
        path = "/api/v3/members/me"
        response = self._send_request('GET', path)
        
        accounts = response.get('accounts', [])
        for acc in accounts:
            if acc.get('currency') == asset.lower():
                return float(acc.get('balance', 0))
        return 0.0

    def get_position(self, symbol):
        # 簡易的 base asset 萃取邏輯
        base_asset = symbol.lower().replace('usdt', '').replace('twd', '')
        if not base_asset or base_asset == symbol.lower():
            base_asset = symbol[:3].lower() 
            
        return self.get_money(asset=base_asset)


# 3. 交易模組：繼承 Base，專門放 POST/DELETE 類型的危險操作
class MaxTradeAPI(MaxBaseAPI):
    def market_order(self, symbol, side, quantity):
        path = "/api/v3/orders"
        params = {
            'market': symbol.lower(),
            'side': side.lower(),
            'ord_type': 'market',
            'volume': str(quantity) 
        }
        return self._send_request('POST', path, params)
        
    def cancel_all_orders(self, symbol):
        """順便幫你把稍早測試的刪單功能加進來"""
        path = "/api/v3/wallet/spot/orders"
        params = {
            'market': symbol.lower()
        }
        return self._send_request('DELETE', path, params)
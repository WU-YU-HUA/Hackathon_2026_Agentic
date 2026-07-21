from decimal import Decimal
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


class MaxQueryAPI(MaxBaseAPI):
    """資產模組"""
    def __init__(self, key, secret, cache_ttl=60):
        super().__init__(key, secret)
        self.assets = {}
        self.last_update_time = 0.0  # 紀錄最後一次成功更新的時間戳記
        self.cache_ttl = cache_ttl   # 快取存活時間 (預設 60 秒)

    def _is_cache_expired(self):
        """判斷內部快取是否已經過期"""
        return (time.time() - self.last_update_time) > self.cache_ttl or not self.assets
    
    def get_all_balance(self):
        """強制發送 API 請求更新資料，更新總資產"""
        path = "/api/v3/wallet/spot/accounts"
        response = self._send_request('GET', path)
        
        self.assets.clear()
        for acc in response:
            balance = float(acc.get('balance', 0))
            if balance > 0:
                currency = acc.get('currency').lower()
                self.assets[currency] = balance
                
        # 更新完畢後，把最後更新時間設為「現在」
        self.last_update_time = time.time()
        return self.assets

    def get_money(self, asset="usdt"):
        """取得單一幣種餘額 (具備自動快取保護)"""
        if self._is_cache_expired():
            self.get_all_balance()
            
        return self.assets.get(asset.lower(), 0.0)

    def get_position(self, symbol):
        # 簡易的 base asset 萃取邏輯
        base_asset = symbol.lower().replace('usdt', '').replace('twd', '')
        if not base_asset or base_asset == symbol.lower():
            base_asset = symbol[:3].lower() 
            
        return self.get_money(asset=base_asset)


class MaxTradeAPI(MaxBaseAPI):
    """交易模組"""
    def market_order(self, symbol, side, quantity):
        """市價單"""
        path = "/api/v3/wallet/spot/order"
        params = {
            'market': symbol.lower(),
            'side': side.lower(),
            'ord_type': 'market',
            'volume': str(quantity) 
        }
        return self._send_request('POST', path, params)
    
    def limit_order(self, symbol, side, price, quantity):
        """限價單"""
        path = "/api/v3/wallet/spot/order"
        
        params = {
            'market': symbol.lower(),
            'side': side.lower(),
            'ord_type': 'limit',       # 限價單
            'price': str(price),       # 限價單必須提供 price (價格)
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
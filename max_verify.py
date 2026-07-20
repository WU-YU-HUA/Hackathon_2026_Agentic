import os
import time
import json
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

# 載入當前目錄下的 .env 檔案
load_dotenv()

# 透過 os.getenv 讀取環境變數
access_key = os.getenv('MAX_ACCESS')
secret_key = os.getenv('MAX_SECRET')
base_url = 'https://max-api.maicoin.com'

# 簡單的錯誤檢查，確保有成功讀取到金鑰
if not access_key or not secret_key:
    raise ValueError("找不到 API 金鑰，請確認 .env 檔案是否設定正確。")

def get_info():
    path = '/api/v3/info'
    nonce = int(time.time() * 1000)

    params = {
        'nonce': nonce
    }

    params_to_be_signed = params.copy()
    params_to_be_signed['path'] = path

    json_str = json.dumps(params_to_be_signed, separators=(',', ':'))
    payload = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        'X-MAX-ACCESSKEY': access_key,
        'X-MAX-PAYLOAD': payload,
        'X-MAX-SIGNATURE': signature,
        'Content-Type': 'application/json',
    }

    url = base_url + path
    response = requests.get(url, params=params, headers=headers)
    
    print("=== GET /api/v3/info ===")
    print(response.json())


def delete_orders():
    path = '/api/v3/wallet/spot/orders'
    nonce = int(time.time() * 1000)

    params = {
        'nonce': nonce,
        'market': 'btcusdt',
    }

    params_to_be_signed = params.copy()
    params_to_be_signed['path'] = path

    json_str = json.dumps(params_to_be_signed, separators=(',', ':'))
    payload = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        'X-MAX-ACCESSKEY': access_key,
        'X-MAX-PAYLOAD': payload,
        'X-MAX-SIGNATURE': signature,
        'Content-Type': 'application/json',
    }

    url = base_url + path
    response = requests.delete(url, json=params, headers=headers)
    
    print("\n=== DELETE /api/v3/wallet/spot/orders ===")
    print(response.json())


if __name__ == '__main__':
    get_info()
    delete_orders()
# api/getData.py
import json
import boto3
from botocore.exceptions import ClientError

LAMBDA_FUNCTION_NAME = "crypto-kline"
AWS_REGION = "us-west-2"

def fetch_technical_data(test_name: str, payload: dict) -> dict:
    """呼叫 AWS Lambda 並回傳 15m, 1h, 6h, 1d 等技術數據字典"""
    print(f"\n==========================================")
    print(f"🚀 執行: {test_name}")
    print(f"==========================================")

    client = boto3.client("lambda", region_name=AWS_REGION)

    try:
        response = client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        if "FunctionError" in response_payload:
            print(f"❌ Lambda 執行失敗: {response_payload}")
            return {}

        body_str = response_payload.get("body", "{}")
        body = json.loads(body_str) if isinstance(body_str, str) else body_str
        
        # 🌟 記得要 return body
        return body if isinstance(body, dict) else {}

    except Exception as e:
        print(f"❌ 呼叫失敗: {e}")
        return {}


if __name__ == "__main__":
    test_1 = {"symbol": "BTCUSDT"}
    res = fetch_technical_data("1. 直接呼叫 - BTC 數據", test_1)
    print("回傳 Keys:", res.keys() if res else "無資料")
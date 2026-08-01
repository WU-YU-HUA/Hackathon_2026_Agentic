import json
import boto3
from botocore.exceptions import ClientError

# ==================== 設定區 ====================
# 請替換為你在 AWS Console 上的 Lambda 函數名稱
LAMBDA_FUNCTION_NAME = "crypto-social"
AWS_REGION = "us-west-2"
# ================================================


def invoke_lambda(test_name: str, payload: dict):
    """呼叫 AWS Lambda 並解析結果"""
    print(f"\n==========================================")
    print(f"🚀 執行測試: {test_name}")
    print(f"==========================================")

    # 初始化 AWS Lambda Client
    client = boto3.client("lambda", region_name=AWS_REGION)

    try:
        # 呼叫遠端 Lambda
        response = client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",  # 同步呼叫
            Payload=json.dumps(payload),
        )

        # 讀取並解碼回傳 Payload
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        # 檢查 Lambda 是否崩潰
        if "FunctionError" in response:
            print("❌ Lambda 執行發生未捕獲異常:")
            print(json.dumps(response_payload, indent=2, ensure_ascii=False))
            return

        status_code = response_payload.get("statusCode")
        body_str = response_payload.get("body", "{}")

        print(f"📌 Status Code: {status_code}")

        # 解析 Body
        try:
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
            print("📄 回傳內容 (Body):")
            print(json.dumps(body, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(f"📄 回傳原始內容: {body_str}")

    except ClientError as e:
        print(f"❌ AWS API 呼叫失敗: {e}")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")


if __name__ == "__main__":
    # 測試 1: 直接呼叫 (BTC, 當天恐懼貪婪指數 + 社群投票)
    test_1 = {"symbol": "btc", "limit": 1}
    invoke_lambda("1. 直接呼叫 - BTC 社群情緒與即時恐懼指數", test_1)
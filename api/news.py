import json
import boto3
from botocore.exceptions import ClientError

# ==================== 設定區 ====================
# 請替換成你在 AWS 上建立的 Lambda 函數名稱
LAMBDA_FUNCTION_NAME = "crypto-news"  # 例如：crypto-news
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
            InvocationType="RequestResponse",  # 同步呼叫 (等待回傳)
            Payload=json.dumps(payload),
        )

        # 讀取並解碼回傳 Payload
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        print(f"📌 Lambda 執行狀態碼 (AWS): {response['StatusCode']}")

        # 處理 Function Error (如果 Python 程式內 crash)
        if "FunctionError" in response:
            print(f"❌ Lambda 執行發生未捕獲異常:")
            print(json.dumps(response_payload, indent=2, ensure_ascii=False))
            return

        # 解析你的 Handler 回傳格式
        status_code = response_payload.get("statusCode")
        body_str = response_payload.get("body", "{}")

        print(f"📌 Handler 回傳 HTTP Status: {status_code}")

        # 嘗試解析 body (因為你的 handler 做了 json.dumps)
        try:
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
            print("📄 回傳內容 (Body):")
            print(json.dumps(body, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(f"📄 回傳原始內容: {body_str}")

    except ClientError as e:
        print(f"❌ AWS API 呼叫失敗: {e}")
    except Exception as e:
        print(f"❌ 發生非預期錯誤: {e}")


if __name__ == "__main__":
    # 測試 1: 直接呼叫 (Direct Event)
    test_1_event = {"tag": "BTC"}
    invoke_lambda("1. 直接呼叫 (Direct Call)", test_1_event)

    # 測試 2: 模擬 API Gateway GET 請求
    test_2_event = {"queryStringParameters": {"tag": "ethereum"}}
    invoke_lambda("2. 模擬 API Gateway GET", test_2_event)

    # 測試 3: 模擬 API Gateway POST 請求
    test_3_event = {"body": json.dumps({"tag": "solana"})}
    invoke_lambda("3. 模擬 API Gateway POST", test_3_event)
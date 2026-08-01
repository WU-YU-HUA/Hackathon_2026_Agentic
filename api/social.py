import json
import boto3
from botocore.exceptions import ClientError

# ==================== 設定區 ====================
LAMBDA_FUNCTION_NAME = "crypto-social"
AWS_REGION = "us-west-2"
# ================================================


def get_vote_feargreed(test_name: str, payload: dict) -> dict:
    """呼叫 AWS Lambda 並回傳合併後的社群投票與恐懼貪婪指數"""
    print(f"\n==========================================")
    print(f"🚀 執行: {test_name}")
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
        if "FunctionError" in response_payload:
            print("❌ Lambda 執行發生未捕獲異常:")
            print(json.dumps(response_payload, indent=2, ensure_ascii=False))
            return {}

        status_code = response_payload.get("statusCode")
        body_str = response_payload.get("body", "{}")

        print(f"📌 Status Code: {status_code}")

        # 解析 Body 並回傳
        body = json.loads(body_str) if isinstance(body_str, str) else body_str
        
        # 🌟 關鍵：將解析出來的字典 return 出去
        return body if isinstance(body, dict) else {}

    except ClientError as e:
        print(f"❌ AWS API 呼叫失敗: {e}")
        return {}
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return {}


if __name__ == "__main__":
    # 測試：直接呼叫 (BTC, 當天恐懼貪婪指數 + 社群投票)
    test_1 = {"symbol": "btc", "limit": 1}
    res = get_vote_feargreed("1. 直接呼叫 - BTC 社群情緒與即時恐懼指數", test_1)
    print("📄 回傳結果字典：", res)
import boto3
import json
from social import get_vote_feargreed

lambda_client = boto3.client('lambda', region_name='us-west-2')


def invoke_social_analyzer(symbol, fear_and_greed, community_sentiment):
    """
    同步呼叫 crypto-social-ai-analyzer，等待 Bedrock 完成情緒面分析並取得結果。

    參數:
        symbol: 例如 "BTC"
        fear_and_greed: list，例如 [{"value":27,"sentiment":"Fear","timestamp":...}, ...]
        community_sentiment: dict，例如 {"symbol":"BTC","coingecko_id":"bitcoin",
                                          "up_percentage":67.32,"down_percentage":32.68}
    """
    # 這裡的 key 必須對齊 crypto-social-ai-analyzer 的 parse_input() 預期格式：
    # event = {"symbol": ..., "sentiment_data": {"fear_and_greed": [...], "community_sentiment": {...}}}
    payload_dict = {
        'symbol': symbol,
        'sentiment_data': {
            'symbol': symbol,
            'fear_and_greed': fear_and_greed,
            'community_sentiment': community_sentiment
        }
    }

    try:
        print(f"準備呼叫 crypto-social-ai-analyzer，標的: {symbol}...")
        response = lambda_client.invoke(
            FunctionName='crypto-social-ai-analyzer',
            InvocationType='RequestResponse',  # 同步，等待執行完
            Payload=json.dumps(payload_dict)
        )

        result_payload = json.loads(response['Payload'].read().decode('utf-8'))

        # 1. 檢查 Lambda 系統層級錯誤 (如 OOM、Timeout 或未捕捉的例外)
        if 'FunctionError' in response:
            print(f"Analyzer Lambda 系統錯誤: {result_payload}")
            raise Exception(f"crypto-social-ai-analyzer 崩潰或超時: "
                             f"{result_payload.get('errorMessage', result_payload)}")

        # 2. 解析業務內容 (處理 API Gateway 格式回傳值)
        # 正常執行完的話，result_payload 長這樣：
        # {"statusCode": 200/500, "headers": {...}, "body": "...(JSON string)..."}
        body_content = result_payload.get('body', '{}')
        body = json.loads(body_content) if isinstance(body_content, str) else body_content

        if result_payload.get('statusCode') != 200:
            raise Exception(f"Analyzer 業務邏輯錯誤: {body.get('error', '未知錯誤')}")

        print("成功取得 crypto-social-ai-analyzer 分析結果！")
        return body  # 真正的分析結果 (recommendation, confidence, sentiment_regime...)

    except Exception as e:
        print(f"呼叫 crypto-social-ai-analyzer 時發生例外: {str(e)}")
        raise e


# ==========================================
# 🧪 測試執行入口
# ==========================================
if __name__ == "__main__":
    TEST_SYMBOL = "BTC"

    print("=" * 50)
    print(f"開始執行端到端測試 - 標的: {TEST_SYMBOL}")
    print("=" * 50)

    # 📌 步驟 1: 從 api.social 抓取社群情緒與恐懼貪婪指數
    print("\n[步驟 1/2] 正在從 api.social 獲取社群情緒數據...")
    social_data = get_vote_feargreed(
        test_name="測試獲取社群情緒與恐懼貪婪指數",
        payload={"symbol": TEST_SYMBOL, "limit": 7}
    )

    if not social_data:
        print("⚠️ 無法獲取社群情緒數據，測試中止。")
    else:
        print(f"✅ 成功獲取社群情緒數據！內容包含：{list(social_data.keys())}")

        fear_and_greed = social_data.get("fear_and_greed", [])
        community_sentiment = social_data.get("community_sentiment", {})

        # 📌 步驟 2: 傳給 AI Analyzer 進行分析
        print("\n[步驟 2/2] 正在將數據發送給 crypto-social-ai-analyzer...")
        try:
            analysis_result = invoke_social_analyzer(
                symbol=TEST_SYMBOL,
                fear_and_greed=fear_and_greed,
                community_sentiment=community_sentiment
            )

            # 📌 步驟 3: 格式化輸出分析結果
            print("\n" + "=" * 20 + " 🎯 最終 AI 分析結果 " + "=" * 20)
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            print("=" * 60)

        except Exception as err:
            print(f"\n❌ 測試過程發生錯誤: {err}")

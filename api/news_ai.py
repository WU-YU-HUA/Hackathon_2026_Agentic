import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-west-2')


def invoke_analyzer(news_data, tag):
    """
    同步呼叫 crypto-news-ai-analyzer (B)，等待並取得分析結果。
    """
    response = lambda_client.invoke(
        FunctionName='crypto-news-ai-analyzer',
        InvocationType='RequestResponse',  # 同步，等待 B 執行完
        Payload=json.dumps({
            'tag': tag,
            'count': len(news_data),
            'news': news_data
        })
    )

    result_payload = json.loads(response['Payload'].read())

    if 'FunctionError' in response:
        # B 端 unhandled exception，result_payload 長這樣：
        # {"errorMessage": "...", "errorType": "...", "stackTrace": [...]}
        print(f"Analyzer Lambda error: {result_payload}")
        raise Exception(f"Analyzer Lambda failed: {result_payload.get('errorMessage', result_payload)}")

    # B 正常執行完的話，result_payload 是 B 的完整回傳
    # {"statusCode": 200/500, "headers": {...}, "body": "...(JSON string)..."}
    body = json.loads(result_payload.get('body', '{}'))

    if result_payload.get('statusCode') != 200:
        raise Exception(f"Analyzer returned error: {body.get('error', 'unknown error')}")

    return body  # 真正的分析結果 (overall_sentiment, key_events, summary...)



def main():
    """
    測試流程：
    1. 先呼叫 news.py 的 fetch_news 取得新聞資料
    2. 再把資料交給 invoke_analyzer 非同步觸發 B (crypto-news-ai-analyzer)
    """
    from news import fetch_news

    tag = "BTC"

    news_data = fetch_news(tag)[:-5]

    if not news_data:
        print("⚠️ 沒有取得任何新聞資料，跳過觸發 analyzer。")
        return

    response = invoke_analyzer(news_data, tag)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print("✅ 測試流程結束")


if __name__ == "__main__":
    main()

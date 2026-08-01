import boto3
import json
 
lambda_client = boto3.client('lambda', region_name='us-west-2')
 
 
def invoke_analyzer(news_data, tag):
    """
    非同步觸發 crypto-news-ai-analyzer (B)。
    A 不需要等待或處理 B 的回傳結果，B 會自己存 DB / 發通知。
    """
    try:
        response = lambda_client.invoke(
            FunctionName='crypto-news-ai-analyzer',
            InvocationType='Event',  # 非同步，A 丟出去就結束，不等待
            Payload=json.dumps({
                'tag': tag,
                'count': len(news_data),
                'news': news_data
            })
        )
 
        # Event 模式下，成功送出的話 StatusCode 會是 202（不是 200）
        # 這只代表「Lambda 已接收這個呼叫」，不代表 B 執行成功或失敗
        status_code = response.get('StatusCode')
        if status_code == 202:
            print(f"Successfully triggered analyzer for tag={tag}, news_count={len(news_data)}")
        else:
            print(f"Unexpected StatusCode when invoking analyzer: {status_code}")
    except Exception as e:
        # 觸發失敗（例如權限不足、B 不存在）在這裡才會看到
        # 但 B 自己執行過程中的錯誤，A 完全看不到，要去 B 的 CloudWatch logs 查
        print(f"Failed to invoke analyzer: {str(e)}")
        raise


def main():
    """
    測試流程：
    1. 先呼叫 news.py 的 fetch_news 取得新聞資料
    2. 再把資料交給 invoke_analyzer 非同步觸發 B (crypto-news-ai-analyzer)
    """
    # 支援直接執行 (python api/news_ai.py) 與模組匯入兩種情境
    try:
        from news import fetch_news
    except ImportError:
        from api.news import fetch_news

    tag = "BTC"

    print(f"==========================================")
    print(f"🚀 步驟 1: 從 news.py 取得 tag={tag} 的新聞資料")
    print(f"==========================================")
    news_data = fetch_news(tag)

    if not news_data:
        print("⚠️ 沒有取得任何新聞資料，跳過觸發 analyzer。")
        return

    print(f"\n==========================================")
    print(f"🚀 步驟 2: 觸發 analyzer (crypto-news-ai-analyzer)")
    print(f"==========================================")
    invoke_analyzer(news_data, tag)
    print("✅ 測試流程結束")


if __name__ == "__main__":
    main()

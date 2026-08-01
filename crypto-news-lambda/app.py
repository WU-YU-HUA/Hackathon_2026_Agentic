"""
AWS Lambda Handler for Crypto News Service
支援 API Gateway 整合
"""

import json
from news import fetch_crypto_news


def handler(event, context):
    """
    AWS Lambda 進入點
    
    支援的呼叫方式：
    1. 直接呼叫: {"tag": "bitcoin"}
    2. API Gateway GET: /news?tag=bitcoin
    3. API Gateway POST: body = {"tag": "bitcoin"}
    """
    
    try:
        tag = None
        
        # 方式 1: API Gateway GET (Query String)
        if event.get("queryStringParameters"):
            tag = event["queryStringParameters"].get("tag")
        
        # 方式 2: API Gateway POST (Body)
        elif event.get("body"):
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
            tag = body.get("tag")
        
        # 方式 3: 直接 Lambda 呼叫
        elif event.get("tag"):
            tag = event.get("tag")
        
        # 呼叫新聞抓取函式
        result = fetch_crypto_news(tag=tag)
        
        # 檢查是否有錯誤
        if isinstance(result, dict) and "error" in result:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(result, ensure_ascii=False)
            }
        
        # 成功回傳
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "tag": tag,
                "count": len(result),
                "news": result
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}"
            }, ensure_ascii=False)
        }
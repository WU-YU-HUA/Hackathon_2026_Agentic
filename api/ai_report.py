#api/ai_report.py
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-west-2')


def invoke_summary_analyzer(symbol, risk_level, technical_report, social_report, news_report):
    """
    同步呼叫彙整服務 (Lambda D)，等待 Bedrock 完成三份 report 的彙整分析並取得最終結果。

    參數:
        symbol: 例如 "BTC"
        risk_level: 使用者風險偏好，1-10 的整數
        technical_report: crypto-kline-ai-analyzer 回傳的 dict (recommendation, confidence, ...)
        social_report: crypto-social-ai-analyzer 回傳的 dict (recommendation, confidence, ...)
        news_report: crypto-news-ai-analyzer 回傳的 dict (overall_sentiment, key_events, ...)
    """
    payload_dict = {
        'symbol': symbol,
        'risk_level': risk_level,
        'reports': {
            'technical_report': technical_report,
            'social_report': social_report,
            'news_report': news_report
        }
    }

    try:
        print(f"準備呼叫彙整服務 (Lambda D)，標的: {symbol}, 風險等級: {risk_level}...")
        response = lambda_client.invoke(
            FunctionName='crypto-summary-ai-analyzer',  # 請依你實際部署的名稱調整
            InvocationType='RequestResponse',
            Payload=json.dumps(payload_dict)
        )

        result_payload = json.loads(response['Payload'].read().decode('utf-8'))

        if 'FunctionError' in response:
            print(f"Summary Analyzer Lambda 系統錯誤: {result_payload}")
            raise Exception(f"彙整服務崩潰或超時: {result_payload.get('errorMessage', result_payload)}")

        body_content = result_payload.get('body', '{}')
        body = json.loads(body_content) if isinstance(body_content, str) else body_content

        if result_payload.get('statusCode') != 200:
            raise Exception(f"彙整服務業務邏輯錯誤: {body.get('error', '未知錯誤')}")

        print("成功取得彙整服務最終報告！")
        return body  # {market_assessment, personalized_strategy, risk_factors, report_markdown, ...}

    except Exception as e:
        print(f"呼叫彙整服務時發生例外: {str(e)}")
        raise e

# ==========================================
# 🧪 測試執行入口
# ==========================================
def main():
    """
    端到端測試流程：
    1. 從 getData / news / social 抓取原始資料
    2. 分別交給 kline_ai / news_ai / social_ai 三個 analyzer 取得三份 report
    3. 將三份 report 餵給 invoke_summary_analyzer 產出最終彙整報告
    """
    from getData import fetch_technical_data
    from kline_ai import invoke_kline_analyzer
    from news import fetch_news
    from news_ai import invoke_analyzer as invoke_news_analyzer
    from social import get_vote_feargreed
    from social_ai import invoke_social_analyzer

    TEST_SYMBOL = "BTC"
    RISK_LEVEL = 5  # 使用者風險偏好 1-5

    print("=" * 60)
    print(f"開始執行彙整報告端到端測試 - 標的: {TEST_SYMBOL}, 風險等級: {RISK_LEVEL}")
    print("=" * 60)

    # 📌 步驟 1: 技術面 (kline_ai)
    print("\n[步驟 1/4] 產生技術面分析 (kline_ai)...")
    kline_data = fetch_technical_data(
        test_name="彙整報告測試 - 技術指標",
        payload={"symbol": TEST_SYMBOL}
    )
    if not kline_data:
        print("⚠️ 無法取得 K 線數據，測試中止。")
        return
    technical_report = invoke_kline_analyzer(
        symbol=TEST_SYMBOL,
        kline_data=kline_data.get("data", {})
    )

    # 📌 步驟 2: 新聞面 (news_ai)
    print("\n[步驟 2/4] 產生新聞面分析 (news_ai)...")
    news_data = fetch_news(TEST_SYMBOL)
    if not news_data:
        print("⚠️ 無法取得新聞資料，測試中止。")
        return
    news_report = invoke_news_analyzer(news_data, TEST_SYMBOL)

    # 📌 步驟 3: 情緒面 (social_ai)
    print("\n[步驟 3/4] 產生情緒面分析 (social_ai)...")
    social_data = get_vote_feargreed(
        test_name="彙整報告測試 - 社群情緒",
        payload={"symbol": TEST_SYMBOL, "limit": 7}
    )
    if not social_data:
        print("⚠️ 無法取得社群情緒數據，測試中止。")
        return
    social_report = {}

    # 📌 步驟 4: 彙整 (ai_report)
    print("\n[步驟 4/4] 將三份 report 交給 crypto-summary-ai-analyzer 彙整...")
    try:
        final_report = invoke_summary_analyzer(
            symbol=TEST_SYMBOL,
            risk_level=RISK_LEVEL,
            technical_report=technical_report,  # kline 分析結果
            social_report=social_report,        # 情緒分析結果
            news_report=news_report             # 新聞分析結果
        )

        print("\n" + "=" * 20 + " 🎯 最終彙整報告 " + "=" * 20)
        print(json.dumps(final_report, indent=2, ensure_ascii=False))
        print("=" * 60)

    except Exception as err:
        print(f"\n❌ 測試過程發生錯誤: {err}")


if __name__ == "__main__":
    main()
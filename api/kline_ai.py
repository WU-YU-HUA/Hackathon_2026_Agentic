import boto3
import json
from getData import fetch_technical_data

# 初始化 Lambda Client (請確保 Region 與部署區一致)
lambda_client = boto3.client('lambda', region_name='us-west-2')

def invoke_kline_analyzer(symbol, kline_data):
    """
    同步呼叫 crypto-kline-ai-analyzer (B)，等待 Bedrock 完成分析並取得結果。
    """
    # 準備傳給 B 的 Payload
    payload_dict = {
        'symbol': symbol,
        'kline_data': kline_data
    }

    try:
        print(f"🚀 準備呼叫 crypto-kline-ai-analyzer，標的: {symbol}...")
        response = lambda_client.invoke(
            FunctionName='crypto-kline-ai-analyzer',
            InvocationType='RequestResponse',  # 同步，等待 B 執行完
            Payload=json.dumps(payload_dict)
        )

        # 讀取並反序列化 B 回傳的 Payload
        result_payload = json.loads(response['Payload'].read().decode('utf-8'))

        # 1. 檢查 Lambda 系統層級錯誤 (如 B 發生 OOM、Timeout 或語法錯誤)
        if 'FunctionError' in response:
            error_msg = result_payload.get('errorMessage', str(result_payload))
            print(f"❌ Analyzer Lambda 系統錯誤: {result_payload}")
            raise Exception(f"crypto-kline-ai-analyzer 崩潰或超時: {error_msg}")

        # 2. 解析 B 回傳的業務內容 (處理 API Gateway 格式回傳值)
        if isinstance(result_payload, dict) and 'body' in result_payload:
            body_content = result_payload['body']
            
            # 如果 body 是字串，將其解析為字典；如果已經是字典則直接使用
            body = json.loads(body_content) if isinstance(body_content, str) else body_content
            
            # 檢查業務邏輯是否成功
            status_code = result_payload.get('statusCode')
            if status_code != 200:
                error_detail = body.get('error', '未知錯誤')
                raise Exception(f"Analyzer 業務邏輯錯誤 (HTTP {status_code}): {error_detail}")
            
            print("✅ 成功取得 crypto-kline-ai-analyzer 分析結果！")
            return body
            
        else:
            # 預防 B 沒有包裝 statusCode，而是直接回傳 JSON 結果
            return result_payload

    except Exception as e:
        print(f"❌ 呼叫 crypto-kline-ai-analyzer 時發生例外: {str(e)}")
        raise e


# ==========================================
# 🧪 測試執行入口
# ==========================================
if __name__ == "__main__":
    TEST_SYMBOL = "BTCUSDT"
    
    print("=" * 50)
    print(f"開始執行端到端測試 - 標的: {TEST_SYMBOL}")
    print("=" * 50)
    
    # 📌 步驟 1: 從 api.getData 抓取 K 線數據
    print("\n[步驟 1/2] 正在從 api.getData 獲取 K 線數據...")
    kline_data = fetch_technical_data(
        test_name="測試獲取技術指標數據", 
        payload={"symbol": TEST_SYMBOL}
    )
    
    if not kline_data:
        print("⚠️ 無法獲取 K 線數據，測試中止。")
    else:
        print(f"✅ 成功獲取 K 線數據！內容包含：{list(kline_data.keys())}")
        print(kline_data.get('data').keys())
        # 📌 步驟 2: 傳給 AI Analyzer 進行分析
        print("\n[步驟 2/2] 正在將數據發送給 crypto-kline-ai-analyzer...")
        try:
            analysis_result = invoke_kline_analyzer(
                symbol=TEST_SYMBOL, 
                kline_data=kline_data.get("data", {})
            )
            
            # 📌 步驟 3: 格式化輸出分析結果
            print("\n" + "=" * 20 + " 🎯 最終 AI 分析結果 " + "=" * 20)
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            print("=" * 60)
            
        except Exception as err:
            print(f"\n❌ 測試過程發生錯誤: {err}")
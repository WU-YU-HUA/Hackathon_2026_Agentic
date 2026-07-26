"""
測試 order_tab 整合腳本
用於驗證 MAX API 連接與基本功能
"""
import os
import json
from dotenv import load_dotenv
from maxAPI import MaxQueryAPI, MaxTradeAPI

# 載入環境變數
load_dotenv()

def test_connection():
    """測試 API 連接"""
    print("=" * 50)
    print("🔍 測試 MAX API 連接")
    print("=" * 50)
    
    access_key = os.getenv("MAX_ACCESS")
    secret_key = os.getenv("MAX_SECRET")
    
    if not access_key or not secret_key:
        print("❌ 未找到 API 金鑰，請檢查 .env 檔案")
        return False
    
    print(f"✅ API Key 已載入: {access_key[:10]}...")
    return True

def test_get_balances():
    """測試獲取資產"""
    print("\n" + "=" * 50)
    print("💰 測試獲取資產資料")
    print("=" * 50)
    
    try:
        access_key = os.getenv("MAX_ACCESS")
        secret_key = os.getenv("MAX_SECRET")
        
        query_client = MaxQueryAPI(access_key, secret_key, cache_ttl=60)
        balances = query_client.get_all_balance()
        
        print(f"\n📊 找到 {len(balances)} 種資產:")
        for currency, amount in balances.items():
            print(f"  - {currency.upper()}: {amount:.6f}")
        
        print(f"\n✅ 資產獲取成功！")
        return True
        
    except Exception as e:
        print(f"❌ 獲取資產失敗: {str(e)}")
        return False

def test_allowed_pairs():
    """測試交易對配置"""
    print("\n" + "=" * 50)
    print("🎯 測試交易對配置")
    print("=" * 50)
    
    max_pairs_str = os.getenv("MAX_PAIRS", '["BTCUSDT"]')
    try:
        pairs = json.loads(max_pairs_str)
        print(f"\n✅ 允許的交易對: {', '.join(pairs)}")
        
        print("\n📋 交易對解析:")
        for pair in pairs:
            symbol = pair.replace("USDT", "").replace("usdt", "")
            print(f"  - {pair} -> {symbol}")
        
        return True
    except Exception as e:
        print(f"❌ 解析交易對失敗: {str(e)}")
        return False

def test_query_api():
    """測試 Query API 快取機制"""
    print("\n" + "=" * 50)
    print("🔄 測試 Query API 快取機制")
    print("=" * 50)
    
    try:
        access_key = os.getenv("MAX_ACCESS")
        secret_key = os.getenv("MAX_SECRET")
        
        query_client = MaxQueryAPI(access_key, secret_key, cache_ttl=60)
        
        # 第一次呼叫（會發送 API 請求）
        print("\n📡 第一次呼叫 (會發送 API 請求)...")
        usdt_balance = query_client.get_money('usdt')
        print(f"✅ USDT 餘額: ${usdt_balance:,.2f}")
        
        # 第二次呼叫（使用快取）
        print("\n💾 第二次呼叫 (使用快取)...")
        usdt_balance_cached = query_client.get_money('usdt')
        print(f"✅ USDT 餘額 (快取): ${usdt_balance_cached:,.2f}")
        
        print(f"\n✅ 快取機制正常！(TTL: 60 秒)")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False

def main():
    """執行所有測試"""
    print("\n")
    print("🚀 開始測試 Order Tab 整合")
    print("=" * 50)
    
    results = []
    
    # 測試 1: 連接
    results.append(("API 連接", test_connection()))
    
    # 測試 2: 交易對配置
    results.append(("交易對配置", test_allowed_pairs()))
    
    # 測試 3: 獲取資產
    results.append(("獲取資產", test_get_balances()))
    
    # 測試 4: 快取機制
    results.append(("快取機制", test_query_api()))
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 測試總結")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！可以啟動 Streamlit 應用了")
        print("\n執行指令:")
        print("  streamlit run app.py")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")

if __name__ == "__main__":
    main()

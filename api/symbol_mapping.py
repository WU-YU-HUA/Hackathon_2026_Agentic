"""交易對符號與 CoinGecko ID 的映射表"""

# MAX 交易對 -> CoinGecko ID 映射
SYMBOL_TO_COINGECKO = {
    "BTC": "bitcoin",
    "BTCUSDT": "bitcoin",
    "ETH": "ethereum",
    "ETHUSDT": "ethereum",
    "SOL": "solana",
    "SOLUSDT": "solana",
    "BNB": "binancecoin",
    "BNBUSDT": "binancecoin",
    "XRP": "ripple",
    "XRPUSDT": "ripple",
    "ADA": "cardano",
    "ADAUSDT": "cardano",
    "DOGE": "dogecoin",
    "DOGEUSDT": "dogecoin",
    "MATIC": "matic-network",
    "MATICUSDT": "matic-network",
    "DOT": "polkadot",
    "DOTUSDT": "polkadot",
    "AVAX": "avalanche-2",
    "AVAXUSDT": "avalanche-2",
}

def get_coingecko_id(symbol: str) -> str:
    """
    根據交易對符號獲取對應的 CoinGecko ID
    
    :param symbol: 交易對符號，如 'BTC', 'BTCUSDT', 'ETH' 等
    :return: CoinGecko ID，如果找不到則返回 'bitcoin' 作為預設值
    """
    symbol = symbol.upper().strip()
    
    # 移除常見的交易對後綴
    for suffix in ['USDT', 'TWD', 'USD']:
        if symbol.endswith(suffix):
            base_symbol = symbol[:-len(suffix)]
            if base_symbol in SYMBOL_TO_COINGECKO:
                return SYMBOL_TO_COINGECKO[base_symbol]
    
    # 直接查找
    if symbol in SYMBOL_TO_COINGECKO:
        return SYMBOL_TO_COINGECKO[symbol]
    
    # 預設返回 bitcoin
    print(f"[Warning] 找不到 {symbol} 的 CoinGecko ID，使用預設值 'bitcoin'")
    return "bitcoin"


if __name__ == "__main__":
    # 測試映射
    test_symbols = ["BTC", "BTCUSDT", "ETH", "SOLUSDT", "XRP", "UNKNOWN"]
    
    print("=== 交易對映射測試 ===")
    for symbol in test_symbols:
        coingecko_id = get_coingecko_id(symbol)
        print(f"{symbol:12} -> {coingecko_id}")

"""
抓取 Cointelegraph RSS 新聞資料
來源: https://cointelegraph.com/rss

功能：依主題 (tag) 做來源端搜尋，例如 bitcoin / ethereum / regulation。
回傳格式：[{title, context}]，context 為 RSS 摘要，一次抓取來源提供的全部新聞。

設計為純粹的 Tool/Data 模組，提供給 AI Agent 作為 Context。
僅使用 requests + 內建 xml/html/re，不需額外套件。
"""

import re
import html
import requests
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CryptoAgent/1.0)"}

# 常見代號/交易對 -> Cointelegraph 實際標籤 slug 的對照
# (Cointelegraph 的 tag 多用全名，eth/btc 等縮寫會 404)
# 涵蓋 .env MAX_PAIRS 的幣種：BTC / ETH / SOL / BNB / XRP
TAG_ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "bnb",       # bnb 標籤本身有效
    "xrp": "xrp",       # xrp 標籤本身有效 (ripple 也可)
    "ada": "cardano",
    "doge": "dogecoin",
}

# 交易對常見的計價幣尾綴，會在正規化時去除 (BTCUSDT -> BTC)
QUOTE_SUFFIXES = ("usdt", "usdc", "usd", "busd")


def _normalize_tag(tag):
    """將使用者輸入的代號/交易對正規化為 Cointelegraph 標籤 slug。

    處理流程：轉小寫去空白 -> 去除計價幣尾綴 (USDT 等) -> 套用縮寫對照。
    例如 "BTCUSDT" -> "btc" -> "bitcoin"；"ETH" -> "ethereum"。
    """
    tag = tag.strip().lower()
    for suffix in QUOTE_SUFFIXES:
        if tag.endswith(suffix) and len(tag) > len(suffix):
            tag = tag[: -len(suffix)]
            break
    return TAG_ALIASES.get(tag, tag)


class CryptoNews:
    """抓取並解析 Cointelegraph RSS 新聞源"""

    def __init__(self, tag=None):
        """
        :param tag: 主題標籤 (來源端搜尋，例如 "bitcoin"、"ethereum"、"regulation")；
                    有給就抓該主題的專屬 RSS，回傳的新聞全部與該主題相關。None 表示抓綜合最新新聞。
                    支援常見縮寫與交易對 (eth -> ethereum、BTCUSDT -> bitcoin ...)。
        """
        # 正規化 tag：去尾綴 + 套用縮寫對照 (支援 BTCUSDT / btc / ETH 等)
        if tag:
            tag = _normalize_tag(tag)
        self.tag = tag
        # 有 tag 就用主題專屬 RSS，否則用綜合新聞 RSS
        if tag:
            self.rss_url = f"https://cointelegraph.com/rss/tag/{tag}"
        else:
            self.rss_url = "https://cointelegraph.com/rss"
        self.raw_xml = None

    def fetch(self):
        """從 RSS 端點抓取原始 XML"""
        try:
            response = requests.get(self.rss_url, headers=HEADERS, timeout=10)
            if response.status_code == 404:
                print(f"[CryptoNews Error] 找不到標籤 '{self.tag}' (404)，"
                      f"請確認是 Cointelegraph 使用的標籤名稱 (例如 bitcoin / ethereum)")
                return False
            response.raise_for_status()
            self.raw_xml = response.content
            return True
        except requests.exceptions.RequestException as e:
            print(f"[CryptoNews Error] RSS 請求失敗: {e}")
            return False

    @staticmethod
    def _clean_html(text):
        """移除 HTML 標籤並還原 HTML 實體，取得乾淨的純文字摘要"""
        if not text:
            return ""
        no_tags = re.sub(r"<[^>]+>", "", text)
        return html.unescape(no_tags).strip()

    def get_news(self):
        """解析並回傳新聞列表 (全部)，格式為 [{title, context}]。"""
        if self.raw_xml is None:
            if not self.fetch() or self.raw_xml is None:
                return {"error": "Failed to fetch Cointelegraph RSS"}

        try:
            root = ET.fromstring(self.raw_xml)
            items = root.findall("./channel/item")
            if not items:
                return {"error": "No items found in RSS feed"}

            news_list = []
            for item in items:
                title = (item.findtext("title", default="") or "").strip()
                summary = self._clean_html(item.findtext("description", default=""))
                news_list.append({
                    "title": title,
                    "context": summary,
                })

            return news_list

        except ET.ParseError as e:
            print(f"[CryptoNews Error] XML 解析失敗: {e}")
            return {"error": f"XML parse error: {e}"}
        except Exception as e:
            print(f"[CryptoNews Error] 資料處理失敗: {e}")
            return {"error": str(e)}


def fetch_crypto_news(tag: str = None):
    """Tool 函式：回傳加密貨幣新聞列表 (全部)，格式為 [{title, context}]。

    :param tag: 主題標籤，來源端搜尋 (bitcoin / ethereum / regulation ...)
    """
    news = CryptoNews(tag=tag)
    return news.get_news()


# ==========================================
# 獨立測試執行區塊
# ==========================================
if __name__ == "__main__":
    def _print(result):
        if isinstance(result, dict) and "error" in result:
            print(f"❌ 錯誤: {result['error']}")
            return
        print(f"✅ 成功抓取 {len(result)} 則新聞\n")
        for i, n in enumerate(result, 1):
            print(f"[{i}] {n['title']}")
            print(f"    context: {n['context']}")
            print()

    print("=== 測試: 抓 bitcoin 主題新聞 (全部) ===\n")
    _print(fetch_crypto_news(tag="bitcoin"))

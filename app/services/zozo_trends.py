import requests
from bs4 import BeautifulSoup
import re
import statistics

BASE_URL = "https://zozo.jp/search/"

def get_zozo_trend_data(keyword: str):
    try:
        url = f"{BASE_URL}?p_keyv={keyword}"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        # 件数取得
        count_text = soup.select_one(".search-header__count").text
        item_count = int(re.sub(r"\D", "", count_text))

        items = soup.select(".search-item") # 実際はもう少しセレクタが複雑な場合が多い
        prices = []
        out_of_stock = 0
        sale_count = 0

        for item in items[:20]: # 直近20件でサンプリング
            # 価格
            p_text = item.select_one(".search-item__price")
            if p_text:
                prices.append(int(re.sub(r"\D", "", p_text.text)))
            # 在庫
            if "在庫なし" in item.text:
                out_of_stock += 1
            # セル
            if item.select_one(".search-item__price--sale"):
                sale_count += 1

        avg_price = round(statistics.mean(prices)) if prices else 0
        
        return {
            "item_count": item_count,
            "avg_price": avg_price,
            "out_of_stock_rate": round(out_of_stock / 20 * 100) if items else 0,
            "sale_rate": round(sale_count / 20 * 100) if items else 0
        }
    except Exception as e:
        print(f"ZOZO Data Error: {e}")
        return None

def evaluate_trend(google_value: int, zozo_data: dict):
    """
    Googleトレンド × ZOZOデータからトレンド評価を返す
    """
    if not zozo_data:
        return None

    if google_value >= 70 and zozo_data["out_of_stock_rate"] >= 25:
        return "売れている"

    if google_value >= 70 and zozo_data["item_count"] < 500:
        return "狙い目"

    if google_value >= 70 and zozo_data["item_count"] >= 2000:
        return "競合多"

    if zozo_data["sale_rate"] >= 40:
        return "下降兆候"

    return "様子見"

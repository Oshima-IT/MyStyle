import requests
from bs4 import BeautifulSoup
import re
import statistics

BASE_URL = "https://zozo.jp/search/"

def get_zozo_trend_data(keyword: str):
    # （前回提示したコードと同じ）
    ...
    return {
        "item_count": item_count,
        "avg_price": avg_price,
        "out_of_stock_rate": round(out_of_stock / item_count * 100),
        "sale_rate": round(sale_count / item_count * 100)
    }

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

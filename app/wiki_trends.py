import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

WIKI_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

def _yyyymmdd(dt):
    return dt.strftime("%Y%m%d")

def fetch_pageviews_last_7_days(article, project="en.wikipedia", access="all-access", agent="user"):
    """
    article: Wikipedia記事タイトル（例: 'Street_fashion'）
    returns: [ (date_str, views_int), ... ] length=7
    """
    today = datetime.now(timezone.utc).date()
    end = today - timedelta(days=1)         # 前日まで
    start = end - timedelta(days=6)         # 7日分

    # APIはURLセグメントなのでエンコードが必要
    article_enc = quote(article, safe="")

    url = f"{WIKI_API}/{project}/{access}/{agent}/{article_enc}/daily/{_yyyymmdd(start)}00/{_yyyymmdd(end)}00"

    r = requests.get(url, timeout=8, headers={"User-Agent": "MyStyle-Trends/1.0"})
    r.raise_for_status()
    data = r.json()

    items = data.get("items", [])
    out = []
    for it in items:
        # timestamp: YYYYMMDD00
        ts = it.get("timestamp", "")
        day = ts[:8]
        views = int(it.get("views", 0) or 0)
        out.append((day, views))

    # 念のため日付順に
    out.sort(key=lambda x: x[0])
    return out

def compute_growth(series):
    """
    series: list[(day, views)] length>=2
    growth: (last - first) / max(first,1)
    """
    if not series or len(series) < 2:
        return 0.0
    first = series[0][1]
    last = series[-1][1]
    base = first if first > 0 else 1
    return (last - first) / base

def build_wiki_trend_payload(mapping):
    """
    mapping: dict key=label(for UI) value=article title
    returns payload with ranked trends
    """
    results = []
    for label, info in mapping.items():
        # normalize info
        if isinstance(info, str):
            article = info
            lang = "en"
        elif isinstance(info, dict):
            article = info.get("wiki_article") or info.get("article")
            lang = info.get("lang", "en")
        else:
            continue

        project = f"{lang}.wikipedia"
        
        try:
            s = fetch_pageviews_last_7_days(article, project=project)
            g = compute_growth(s)
            results.append({
                "label": label,
                "article": article,
                "series": [{"day": d, "views": v} for d, v in s],
                "growth": g,
            })
        except Exception as e:
            print(f"Error fetching wiki trend for {article}: {e}")
            continue

    # growth降順
    results.sort(key=lambda x: x["growth"], reverse=True)

    return {
        "source": "Wikimedia Pageviews",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "trends": results,
    }

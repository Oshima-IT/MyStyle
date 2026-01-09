from pytrends.request import TrendReq

def get_trends(keyword="python"):
    pytrends = TrendReq(hl="ja-JP", tz=540)
    # Support list of keywords or single string
    kw_list = keyword if isinstance(keyword, list) else [keyword]
    pytrends.build_payload(kw_list, timeframe="now 7-d")
    data = pytrends.interest_over_time()
    return data

def get_related_queries(keyword="python"):
    pytrends = TrendReq(hl="ja-JP", tz=540)
    pytrends.build_payload([keyword], timeframe="now 7-d")
    related = pytrends.related_queries()
    # 'top'や'rising'がある場合はそれを返す
    if keyword in related and related[keyword]['top'] is not None:
        return related[keyword]['top']
    return None

if __name__ == "__main__":
    print(get_trends("flask"))
    print(get_related_queries("ファッション"))

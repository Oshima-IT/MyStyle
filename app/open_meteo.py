
import requests
from datetime import datetime, timezone

NAGOYA_LAT = 35.183334
NAGOYA_LON = 136.899994

def fetch_nagoya_weather():
    """
    Open-Meteo Forecast API から名古屋の天気を取得し、
    UI/推薦に必要な最小要素をまとめて返す。
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": NAGOYA_LAT,
        "longitude": NAGOYA_LON,
        "timezone": "Asia/Tokyo",
        "current": "temperature_2m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max",
        "forecast_days": 1,
    }

    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()

    # daily は当日 index=0
    d0 = (data.get("daily") or {})
    out = {
        "source": "Open-Meteo",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "location": {"name": "Nagoya", "lat": NAGOYA_LAT, "lon": NAGOYA_LON},
        "current_temp": (data.get("current") or {}).get("temperature_2m"),
        "today_max": (d0.get("temperature_2m_max") or [None])[0],
        "today_min": (d0.get("temperature_2m_min") or [None])[0],
        "precip_prob_max": (d0.get("precipitation_probability_max") or [None])[0],
        "wind_max": (d0.get("windspeed_10m_max") or [None])[0],
    }
    return out

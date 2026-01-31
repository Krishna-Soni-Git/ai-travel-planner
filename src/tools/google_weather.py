from __future__ import annotations

import math
import requests
from typing import Any, Dict, Optional

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_hourly_weather(lat: float, lng: float, hours: int = 240) -> Dict[str, Any]:
    """
    Open-Meteo forecast (max 240h / 10 days).
    Returns hourly arrays + timezone.
    """
    hours = max(1, min(int(hours), 240))
    forecast_days = max(1, min(10, math.ceil(hours / 24)))

    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "wind_speed_10m",
                "relative_humidity_2m",
            ]
        ),
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "wind_speed_10m_max",
            ]
        ),
        "forecast_days": forecast_days,
        "timezone": "auto",
    }

    r = requests.get(OPEN_METEO_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    data["_tool_window_hours"] = hours
    data["_tool_window_days"] = forecast_days
    return data


def summarize_weather_for_date(wx_json: Dict[str, Any], target_date: str) -> Dict[str, Any]:
    """
    Build a business-ready date summary from hourly arrays for YYYY-MM-DD.
    If target_date is outside the returned window, available=False.
    """
    wx_json = wx_json or {}
    hourly = wx_json.get("hourly") or {}
    times = hourly.get("time") or []

    temps = hourly.get("temperature_2m") or []
    feels = hourly.get("apparent_temperature") or []
    probs = hourly.get("precipitation_probability") or []
    wind = hourly.get("wind_speed_10m") or []

    idxs = [i for i, t in enumerate(times) if isinstance(t, str) and t.startswith(target_date)]
    if not idxs:
        return {
            "available": False,
            "target_date": target_date,
            "timezone": wx_json.get("timezone", "local"),
            "reason": "Forecast available up to 10 days only.",
        }

    def _slice(arr):
        return [arr[i] for i in idxs] if arr else []

    temps_d = _slice(temps)
    feels_d = _slice(feels)
    probs_d = _slice(probs)
    wind_d = _slice(wind)

    def _avg(a):
        return (sum(a) / len(a)) if a else None

    def _min(a):
        return min(a) if a else None

    def _max(a):
        return max(a) if a else None

    ref_avg = _avg(feels_d) if feels_d else _avg(temps_d)

    max_precip = _max(probs_d) or 0
    max_wind = _max(wind_d) or 0

    return {
        "available": True,
        "target_date": target_date,
        "timezone": wx_json.get("timezone", "local"),
        "avg_temp_c": ref_avg,
        "min_temp_c": _min(temps_d),
        "max_temp_c": _max(temps_d),
        "max_precip_prob_pct": max_precip,
        "max_wind_kmh": max_wind,
        "umbrella_needed": bool(max_precip >= 40),
    }


def clothes_from_temp(avg_temp_c: Optional[float], max_wind_kmh: float) -> str:
    if avg_temp_c is None:
        clothes = "Dress in layers (forecast detail not available yet)."
    elif avg_temp_c <= 0:
        clothes = "Heavy winter coat, gloves, warm hat, insulated footwear."
    elif avg_temp_c <= 10:
        clothes = "Warm coat or jacket, long pants, closed-toe shoes."
    elif avg_temp_c <= 20:
        clothes = "Light jacket or sweater, comfortable shoes."
    else:
        clothes = "Light clothing, breathable layers, comfortable walking shoes."

    if max_wind_kmh >= 35:
        clothes = clothes.rstrip(".") + " Add a windbreaker (windy)."
    return clothes

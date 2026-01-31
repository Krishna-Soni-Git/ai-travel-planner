from __future__ import annotations
from typing import Any, Dict, Optional

def compute_risk_score(weather: Optional[Dict[str, Any]], air_quality: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """Return risk scores as ints 0-10. Conservative/simple for explainability."""
    weather_risk = 0
    aq_risk = 0

    # Weather risk (based on wind + precip probability if present)
    if isinstance(weather, dict):
        try:
            # open-meteo style: hourly.precipitation_probability / windspeed
            hourly = weather.get("hourly", {})
            probs = hourly.get("precipitation_probability") or []
            winds = hourly.get("wind_speed_10m") or hourly.get("windspeed_10m") or []
            max_prob = max(probs) if probs else 0
            max_wind = max(winds) if winds else 0

            # map to 0-10
            # precip: 0%->0, 100%->10
            weather_risk = min(10, int(round(max_prob / 10)))
            # wind: add up to +3 if very windy
            if max_wind >= 50:
                weather_risk = min(10, weather_risk + 3)
            elif max_wind >= 35:
                weather_risk = min(10, weather_risk + 2)
            elif max_wind >= 25:
                weather_risk = min(10, weather_risk + 1)
        except Exception:
            weather_risk = 0

    # Air quality risk (UAQI)
    if isinstance(air_quality, dict) and not air_quality.get("_error"):
        try:
            indexes = air_quality.get("indexes") or []
            aqi = None
            for idx in indexes:
                if idx.get("code") == "uaqi":
                    aqi = idx.get("aqi")
                    break
            if aqi is None and indexes:
                aqi = indexes[0].get("aqi")

            if isinstance(aqi, (int, float)):
                # UAQI: lower is better; rough mapping:
                # 0-50 -> 0-2, 51-100 -> 3-5, 101-150 -> 6-7, 151-200 -> 8, 201+ -> 9-10
                if aqi <= 50:
                    aq_risk = 2
                elif aqi <= 100:
                    aq_risk = 5
                elif aqi <= 150:
                    aq_risk = 7
                elif aqi <= 200:
                    aq_risk = 8
                else:
                    aq_risk = 10
        except Exception:
            aq_risk = 0

    overall = max(weather_risk, aq_risk)
    return {"weather_risk": int(weather_risk), "air_quality_risk": int(aq_risk), "overall_risk": int(overall)}

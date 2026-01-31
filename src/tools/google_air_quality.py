from __future__ import annotations
import requests
from typing import Any, Dict
from ..config import GOOGLE_MAPS_API_KEY, BAD_AQI_THRESHOLD

AQ_FORECAST_URL = "https://airquality.googleapis.com/v1/forecast:lookup"
AQ_CURRENT_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"

def _post(url: str, body: dict) -> Dict[str, Any]:
    headers = {"X-Goog-Api-Key": GOOGLE_MAPS_API_KEY, "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=body, timeout=30)
    if not r.ok:
        return {"_error": True, "status_code": r.status_code, "body": r.text[:2000], "_url": url}
    return r.json()

def get_air_quality_forecast(lat: float, lng: float) -> Dict[str, Any]:
    # Try forecast first (often unsupported)
    fc = _post(AQ_FORECAST_URL, {"location": {"latitude": lat, "longitude": lng}})
    if not fc.get("_error"):
        fc["_mode"] = "forecast"
        return fc

    # Fallback to current conditions
    cur = _post(AQ_CURRENT_URL, {"location": {"latitude": lat, "longitude": lng}})
    if not cur.get("_error"):
        cur["_mode"] = "current"
        return cur

    fc["_mode"] = "error"
    return fc

def mask_needed_and_count(aq_json: Dict[str, Any]) -> Dict[str, Any]:
    if aq_json.get("_error"):
        return {
            "mask_needed": False,
            "mask_days": 0,
            "detail": f"Air Quality API error {aq_json.get('status_code')}: {aq_json.get('body')}",
        }

    mode = aq_json.get("_mode", "unknown")

    # If forecast exists, compute days with bad AQI
    hours = aq_json.get("hourlyForecasts") or []
    if hours:
        bad_days = set()
        for h in hours:
            dt = h.get("dateTime", "")
            indexes = h.get("indexes") or []
            aqi_val = None
            for idx in indexes:
                if idx.get("code") == "uaqi":
                    aqi_val = idx.get("aqi")
                    break
            if aqi_val is None and indexes:
                aqi_val = indexes[0].get("aqi")
            if aqi_val is not None and aqi_val >= BAD_AQI_THRESHOLD and dt:
                bad_days.add(dt[:10])

        needed = len(bad_days) > 0
        return {
            "mask_needed": needed,
            "mask_days": len(bad_days),
            "detail": (
                f"[forecast] Bad-air days: {sorted(bad_days)}"
                if bad_days else "[forecast] Air looks OK in forecast window."
            ),
        }

    # Current conditions: single recommendation
    indexes = aq_json.get("indexes") or []
    aqi_val = None
    category = None
    for idx in indexes:
        if idx.get("code") == "uaqi":
            aqi_val = idx.get("aqi")
            category = idx.get("category")
            break
    if aqi_val is None and indexes:
        aqi_val = indexes[0].get("aqi")
        category = indexes[0].get("category")

    if aqi_val is None:
        return {"mask_needed": False, "mask_days": 0, "detail": f"[{mode}] No AQI index returned."}

    # IMPORTANT: low AQI means GOOD air, so mask NOT needed.
    needed = aqi_val >= BAD_AQI_THRESHOLD
    return {
        "mask_needed": needed,
        "mask_days": 1 if needed else 0,
        "detail": f"[{mode}] UAQI={aqi_val} ({category}). Threshold={BAD_AQI_THRESHOLD}.",
    }

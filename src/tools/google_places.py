from __future__ import annotations
import requests
from typing import Any, Dict
from ..config import GOOGLE_MAPS_API_KEY

PLACES_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"

def _post_places(text_query: str) -> Dict[str, Any]:
    headers = {
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "Content-Type": "application/json",
        # FieldMask is REQUIRED for Places API v1
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.id",
    }
    body = {"textQuery": text_query}
    r = requests.post(PLACES_TEXT_URL, headers=headers, json=body, timeout=30)
    if not r.ok:
        return {"_error": True, "status_code": r.status_code, "body": r.text[:2000]}
    return r.json()

def resolve_city_to_latlng(city: str) -> Dict[str, Any]:
    res = _post_places(city)
    if res.get("_error"):
        return res
    places = res.get("places") or []
    if not places:
        return {"_error": True, "status_code": 404, "body": f"No places found for city: {city}"}
    p = places[0]
    loc = p.get("location") or {}
    return {
        "city": city,
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "formatted_address": p.get("formattedAddress"),
        "place_id": p.get("id"),
    }

def resolve_place_address(city: str, place_name: str) -> Dict[str, Any]:
    query = f"{place_name}, {city}"
    res = _post_places(query)
    if res.get("_error"):
        return res
    places = res.get("places") or []
    if not places:
        return {"_error": True, "status_code": 404, "body": f"No places found for: {query}"}
    p = places[0]
    loc = p.get("location") or {}
    name = (p.get("displayName") or {}).get("text") if isinstance(p.get("displayName"), dict) else None
    return {
        "query": query,
        "name": name or place_name,
        "formatted_address": p.get("formattedAddress"),
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "place_id": p.get("id"),
    }

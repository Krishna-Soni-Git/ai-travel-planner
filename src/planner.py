# src/planner.py
from typing import List
from .models import CityStop


def build_agent_request(stops: List[CityStop], client_name: str = "") -> str:
    lines = []
    if client_name:
        lines.append(f"Client: {client_name}")

    lines.append("Create a multi-city travel itinerary with times and formatted addresses.")
    lines.append("For each city/day:")
    lines.append("- confirm attractions (or suggest if missing)")
    lines.append("- attach a clean formatted address for each scheduled activity")
    lines.append("- include a short weather summary and whether an umbrella is recommended")
    lines.append("- include a short air-quality summary and whether a mask is recommended")
    lines.append("- include a packing checklist (8+ items) based on conditions + essentials")
    lines.append("")
    lines.append("Trip input:")
    for s in stops:
        lines.append(f"- {s.city} on {s.date}")
        if s.activities:
            for a in s.activities:
                lines.append(f"  * {a}")
        else:
            lines.append("  * (no activities provided; suggest some)")
    lines.append("")
    lines.append("Output MUST be valid JSON only (no markdown, no backticks, no extra text).")
    return "\n".join(lines)


def build_city_explorer_request(
    city: str,
    date: str = "",
    interests: str = "",
    start_time: str = "09:00",
    pace: str = "moderate",
) -> str:
    """
    City Explorer mode: user gives a city (and optionally a date).
    The agent should generate a timed mini-itinerary + addresses.
    """
    lines = []
    lines.append("Create a one-day city visit plan (client-ready).")
    lines.append("")
    lines.append("Input:")
    lines.append(f"- City: {city}")
    lines.append(f"- Start time: {start_time}")
    lines.append(f"- Pace: {pace} (slow/moderate/fast)")
    if date:
        lines.append(f"- Date: {date} (YYYY-MM-DD)")
    if interests:
        lines.append(f"- Interests: {interests}")
    lines.append("")
    lines.append("Tool steps (do these):")
    lines.append("1) Call city_latlng(city) to get lat/lng.")
    lines.append("2) Suggest 4–6 attractions and build a timed schedule.")
    lines.append("3) For each attraction, call place_address(city, place_name) and use ONLY formatted_address in the schedule.")
    lines.append("4) If date is provided, call weather(lat, lng, target_date) and air_quality(lat, lng) and summarize briefly.")
    lines.append("5) Provide a packing checklist (8+ items) based on expected conditions + essentials.")
    lines.append("")
    lines.append("Return ONLY valid JSON in this schema (keys must match exactly):")
    lines.append("{")
    lines.append('  "city": "string",')
    lines.append('  "date": "YYYY-MM-DD or empty",')
    lines.append('  "summary": "string",')
    lines.append('  "schedule": [{"start":"HH:MM","end":"HH:MM","activity":"string","address":"string"}],')
    lines.append('  "tips": ["string"],')
    lines.append('  "weather": "string",')
    lines.append('  "air_quality": "string",')
    lines.append('  "packing": ["string"]')
    lines.append("}")
    return "\n".join(lines)

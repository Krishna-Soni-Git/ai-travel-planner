# src/agent/single_agent.py
from __future__ import annotations

from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool as lc_tool
from langchain_core.messages import SystemMessage

from langgraph.prebuilt import create_react_agent

from ..config import OPENAI_API_KEY, OPENAI_MODEL
from ..tools.google_places import resolve_city_to_latlng, resolve_place_address
from ..tools.google_weather import get_hourly_weather, summarize_weather_for_date, clothes_from_temp
from ..tools.google_air_quality import get_air_quality_forecast, mask_needed_and_count
from ..tools.attractions_llm import suggest_attractions
from ..policy import enforce_policy
from ..risk.risk_score import compute_risk_score


SYSTEM_MESSAGE = (
    "Create professional, client-ready travel itineraries.\n"
    "Return ONLY valid JSON. No markdown, no backticks, no extra text.\n\n"
    "You MUST do the following for EACH city in the input:\n"
    "1) Call city_latlng(city) to get lat/lng.\n"
    "2) For each scheduled activity, call place_address(city, place_name) and set schedule[i].address "
    "to the returned formatted_address (string only).\n"
    "3) Call weather(lat, lng, target_date) using that city's date.\n"
    "   - Put the temperature/rain/wind numbers into insights.weather when available.\n"
    "   - Put exactly 'Yes' or 'No' into insights.umbrella.\n"
    "4) Call air_quality(lat, lng) and summarize into insights.air_quality.\n"
    "5) Packing MUST be a list of at specific items tailored to that city’s conditions.\n\n"
    "Weather wording rules:\n"
    "- If available: insights.weather like: '<min>°C to <max>°C, rain up to <pct>%, wind up to <kmh> km/h'.\n"
    "- If not available: write a short professional sentence (no tool references).\n\n"
    "Air quality wording rules:\n"
    "- Use a short professional summary. If numeric AQI/category exists, include it.\n"
    "- Include whether a mask is recommended based on your tool’s mask field.\n\n"
    "Risk rules:\n"
    "- risk.weather_risk, risk.air_quality_risk, risk.overall_risk MUST be integers 0–10.\n"
    "- overall_risk should reflect the higher of the two unless you have reason to adjust.\n\n"
    "If a city has no activities, you MUST call suggest_attractions(city), build a schedule with times, and still resolve addresses.\n\n"
    "JSON schema (keys must match exactly):\n"
    "{\n"
    '  "executive_summary": "string",\n'
    '  "generated_at": "ISO-8601 string",\n'
    '  "client_name": "string",\n'
    '  "scope": "string",\n'
    '  "cities": [\n'
    "    {\n"
    '      "city": "string",\n'
    '      "date": "YYYY-MM-DD",\n'
    '      "schedule": [{"start":"HH:MM","end":"HH:MM","activity":"string","address":"string"}],\n'
    '      "insights": {"weather":"string","umbrella":"string","air_quality":"string"},\n'
    '      "risk": {"weather_risk":0,"air_quality_risk":0,"overall_risk":0},\n'
    '      "packing": ["string"]\n'
    "    }\n"
    "  ]\n"
    "}\n"
)


def _jsonable(x):
    return x.model_dump() if hasattr(x, "model_dump") else x


@lc_tool("suggest_attractions")
def tool_suggest_attractions(city: str) -> Any:
    """Suggest 4–8 popular attractions for a city (returns JSON list/dict)."""
    enforce_policy(city)
    return _jsonable(suggest_attractions(city))


@lc_tool("city_latlng")
def tool_city_latlng(city: str) -> Dict[str, Any]:
    """Resolve a city to representative lat/lng (returns JSON with keys: city, lat, lng)."""
    enforce_policy(city)
    out = _jsonable(resolve_city_to_latlng(city)) or {}
    return {"city": out.get("city", city), "lat": out.get("lat"), "lng": out.get("lng")}


@lc_tool("place_address")
def tool_place_address(city: str, place_name: str) -> Dict[str, Any]:
    """Resolve a place to a formatted address + lat/lng (returns JSON)."""
    enforce_policy(city)
    out = _jsonable(resolve_place_address(city, place_name)) or {}
    return {
        "place_name": out.get("place_name", place_name),
        "formatted_address": out.get("formatted_address") or out.get("address") or "",
        "lat": out.get("lat"),
        "lng": out.get("lng"),
    }


@lc_tool("weather")
def tool_weather(lat: float, lng: float, target_date: str) -> Dict[str, Any]:
    """Weather for the target date (if within the next 10 days), plus clothes/umbrella + risk score."""
    wx = get_hourly_weather(lat, lng, hours=240)  # 10 days
    day = summarize_weather_for_date(wx, target_date)

    if day.get("available"):
        umbrella = "Yes" if day.get("umbrella_needed") else "No"
        weather_line = (
            f"{day['avg_temp_c']:.1f}°C avg "
            f"({day['min_temp_c']:.1f}°C to {day['max_temp_c']:.1f}°C), "
            f"rain up to {int(round(day['max_precip_prob_pct']))}%, "
            f"wind up to {int(round(day['max_wind_kmh']))} km/h"
        )
        clothes = clothes_from_temp(day.get("avg_temp_c"), float(day.get("max_wind_kmh", 0) or 0))
    else:
        umbrella = "No"
        weather_line = "Forecast will be available when the travel date is within the next 10 days."
        clothes = "Dress in layers; plan based on typical seasonal conditions."

    risk = compute_risk_score(weather=wx, air_quality=None)

    return {
        "available": bool(day.get("available")),
        "timezone": day.get("timezone") or wx.get("timezone", ""),
        "weather_line": weather_line,
        "umbrella": umbrella,
        "clothes": clothes,
        "risk": risk,
    }


@lc_tool("air_quality")
def tool_air_quality(lat: float, lng: float) -> Dict[str, Any]:
    """Current air quality + mask suggestion + risk score (0–10)."""
    aq = get_air_quality_forecast(lat, lng)
    mask = mask_needed_and_count(aq)
    risk = compute_risk_score(weather=None, air_quality=aq)
    return {"raw": aq, "mask": mask, "risk": risk}


class _AgentWithSystemMessage:
    """
    Wrap a LangGraph agent so app.py can keep calling:
      agent.invoke({"messages":[HumanMessage(...)]})
    while we ensure a SystemMessage is always present first.
    """
    def __init__(self, agent, system_text: str):
        self._agent = agent
        self._system = SystemMessage(content=system_text)

    def invoke(self, inputs: Dict[str, Any], **kwargs):
        inputs = dict(inputs or {})
        msgs = list(inputs.get("messages") or [])
        if not msgs or msgs[0].__class__.__name__ != "SystemMessage":
            msgs = [self._system] + msgs
        inputs["messages"] = msgs
        return self._agent.invoke(inputs, **kwargs)


def create_agent_executor():
    """
    Returns a runnable agent compatible with:
      agent.invoke({"messages":[...]}).

    NOTE: Your installed create_react_agent does NOT accept state_modifier,
    so we inject the system message via a wrapper instead.
    """
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)

    tools = [
        tool_suggest_attractions,
        tool_city_latlng,
        tool_place_address,
        tool_weather,
        tool_air_quality,
    ]

    agent = create_react_agent(model=llm, tools=tools)
    return _AgentWithSystemMessage(agent, SYSTEM_MESSAGE)

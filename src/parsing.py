# src/parsing.py
import re
from typing import List
from .models import CityStop

_CITY_RE = re.compile(r"^City\d+\s*:\s*(.+?)\s+(\d{4}-\d{2}-\d{2})\s*$", re.IGNORECASE)

# Accept time formats like:
#  - 8am-9am
#  - 8:00am-9:00am
#  - 08:00-09:00
_TIME_RE = re.compile(
    r"^(?P<place>.+?)(?:\s*;\s*(?P<start>.+?)\s*-\s*(?P<end>.+))?$",
    re.IGNORECASE
)

def parse_trip_text(raw: str) -> List[CityStop]:
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    stops: List[CityStop] = []
    current: CityStop | None = None

    for ln in lines:
        m = _CITY_RE.match(ln)
        if m:
            if current:
                stops.append(current)
            current = CityStop(city=m.group(1).strip(), date=m.group(2).strip(), activities=[])
            continue

        if current is None:
            raise ValueError("Trip must start with a line like: City1: Toronto 2025-01-31")

        # Normalize activity line shape: "Place;start-end" OR "Place"
        tm = _TIME_RE.match(ln)
        if tm:
            place = (tm.group("place") or "").strip()
            start = (tm.group("start") or "").strip()
            end = (tm.group("end") or "").strip()

            if start and end:
                current.activities.append(f"{place};{start}-{end}")
            else:
                current.activities.append(place)
        else:
            # fallback (shouldn't happen often)
            current.activities.append(ln)

    if current:
        stops.append(current)

    if not stops:
        raise ValueError("No cities found. Use: City1: <City> YYYY-MM-DD")

    return stops

from dataclasses import dataclass, field
from typing import List

@dataclass
class CityStop:
    city: str
    date: str  # YYYY-MM-DD
    activities: List[str] = field(default_factory=list)

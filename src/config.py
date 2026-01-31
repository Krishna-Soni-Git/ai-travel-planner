import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")
if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY in .env")

# Mask recommended if AQI >= 101 ("Unhealthy for Sensitive Groups")
BAD_AQI_THRESHOLD = 101

# Travel constraints (course policy)
BLOCKED_COUNTRIES = {"North Korea"}
ALLOWED_REGIONS = {"North America", "Asia"}

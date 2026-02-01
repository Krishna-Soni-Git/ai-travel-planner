from pathlib import Path
from dotenv import load_dotenv

import os

# Force-load .env from the project root (travel_agent_uv/.env)
ROOT = Path(__file__).resolve().parents[1]  # src/ -> project root
load_dotenv(dotenv_path=ROOT / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
BAD_AQI_THRESHOLD = int(os.getenv("BAD_AQI_THRESHOLD", "100"))


if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")
if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY in .env")


# Travel constraints (course policy)
BLOCKED_COUNTRIES = {"North Korea"}
ALLOWED_REGIONS = {"North America", "Asia"}

import logging
logger = logging.getLogger("travel_agent")

if OPENAI_API_KEY:
    logger.info("OPENAI_API_KEY loaded (prefix): %s", OPENAI_API_KEY[:12])
else:
    logger.warning("OPENAI_API_KEY is missing")

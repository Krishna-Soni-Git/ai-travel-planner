from .config import BLOCKED_COUNTRIES, ALLOWED_REGIONS

def enforce_policy(text: str) -> None:
    # Simple guardrail: block specific countries if mentioned
    lowered = text.lower()
    for c in BLOCKED_COUNTRIES:
        if c.lower() in lowered:
            raise ValueError(f"Trips to {c} are not allowed by policy.")

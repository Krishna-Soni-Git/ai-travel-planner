from __future__ import annotations
from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..config import OPENAI_API_KEY, OPENAI_MODEL

def suggest_attractions(city: str) -> List[str]:
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.4)
    msgs = [
        SystemMessage(content="Suggest 5-7 popular, safe tourist attractions for the city. Return ONLY a JSON array of strings."),
        HumanMessage(content=f"City: {city}"),
    ]
    txt = llm.invoke(msgs).content
    # very safe parse: extract JSON array
    import json, re
    m = re.search(r"\[[\s\S]*\]", txt)
    if m:
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list):
                return [str(x) for x in arr][:7]
        except Exception:
            pass
    # fallback
    return ["Downtown walking area", "Main museum", "Top viewpoint", "Local market", "Popular park"]

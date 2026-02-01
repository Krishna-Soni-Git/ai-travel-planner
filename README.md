# 🌍 AI-Powered Travel Planner

An AI-driven travel planning application that generates **client-ready, business-formatted itineraries** using a tool-calling LLM agent and real-time external data (weather, air quality, places, and attractions).

Built with **Streamlit + LangGraph + OpenAI**, producing **structured JSON** outputs with **PDF export** support.

---

## 🚀 Key Features

### 🗺️ Multi-City Trip Planner
- Supports multiple cities and travel dates
- Accepts structured or semi-structured trip input
- Automatically suggests attractions when none are provided
- Resolves **formatted addresses** for each scheduled activity

### 🌆 City Explorer (Single-Day Planner)
- Works with **just a city + date**
- Suggests top attractions with **timed schedules**
- Generates a business-ready one-day visit plan

### 🌦️ Real-World Data Integration
- Live weather forecasts (Open-Meteo)
- Air quality insights + mask recommendations (Google Air Quality)
- Exact place/address resolution (Google Places API)

### 🎒 Smart Packing Checklist
- Tailored to temperature, wind, rain probability, and season
- Ensures **8+ practical packing items** per city

### 📄 Business-Ready Output
- Executive summary
- Timed schedule with addresses
- Conditions & guidance (weather + air quality)
- PDF export using ReportLab

### 🔁 Interactive Updates
- Modify destinations, activities, or timing after generation
- Agent updates the existing itinerary instead of rebuilding from scratch

### Demo Link
- https://www.linkedin.com/posts/krishna-soni-319a191b6_agenticai-langgraph-llm-activity-7423519080160063488-S3m7?utm_source=share&utm_medium=member_desktop&rcm=ACoAADJXJ4UBRMwDhXzF_uqBlAlUrqWoHLgjgCE

---

## 🧠 Tech Stack

- **UI:** Streamlit  
- **Agent Orchestration:** LangGraph (ReAct-style agent)  
- **LLM:** OpenAI via LangChain  
- **Places & Addresses:** Google Places API (v1)  
- **Weather:** Open-Meteo API  
- **Air Quality:** Google Air Quality API  
- **PDF Export:** ReportLab  
- **Dependency Management:** `uv` + `pyproject.toml`

---

## 📁 Project Structure

```txt
travel_agent_uv/
├── app.py                    # Streamlit UI and workflow
├── pyproject.toml            # Dependencies and project config
├── uv.lock                   # Locked dependency versions (uv)
├── src/
│   ├── agent/
│   │   └── single_agent.py   # LangGraph agent + tool wiring
│   ├── tools/
│   │   ├── google_places.py      # City lat/lng + address resolution
│   │   ├── google_weather.py     # Weather retrieval + summary logic
│   │   └── google_air_quality.py # AQI + mask recommendation logic
│   ├── export/
│   │   └── pdf_export.py     # PDF export (ReportLab)
│   ├── parsing.py            # Parses trip input
│   ├── planner.py            # Builds agent prompts
│   ├── config.py             # Loads environment variables
│   └── policy.py             # Input checks / safety rules
└── .env.example              # Example env file (no secrets)

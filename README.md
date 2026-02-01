🌍 AI-Powered Travel Planner

An AI-driven travel planning application that generates client-ready, business-formatted itineraries using large language models and real-time external data (weather, air quality, places, and attractions).

Built with Streamlit + LangGraph + OpenAI, using a tool-calling agent architecture and structured JSON outputs with PDF export support.

🚀 Features

Multi-City Trip Planner

Supports multiple cities and travel dates

Accepts structured or semi-structured trip input

Automatically suggests attractions if none are provided

City Explorer (Single-Day Planner)

Works with just a city and date

Suggests top attractions with optimal timing

Generates a one-day visit plan

Real-World Data Integration

Live weather forecasts

Air quality insights with mask recommendations

Exact, formatted addresses for every activity

Smart Packing Checklist

Tailored to weather, wind, rain, and season

Ensures a minimum of 8 practical items per city

Business-Ready Output

Executive summary

Timed schedules

Conditions & guidance section

Clean, professional formatting

PDF export support

Interactive Updates

Modify destinations, activities, or timing after generation

Agent updates the existing itinerary instead of regenerating from scratch

🧠 Tech Stack

Language: Python

UI: Streamlit

LLM Orchestration: LangChain + LangGraph (ReAct Agent)

LLM Provider: OpenAI API

Maps & Places: Google Places API (v1)

Weather: Open-Meteo API

Air Quality: Google Air Quality API

PDF Export: ReportLab

Dependency Management: uv + pyproject.toml

🎥 Demo

A short demo video is attached on LinkedIn showing:

Trip input

Agent execution

Interactive itinerary updates

PDF export

(https://www.linkedin.com/posts/krishna-soni-319a191b6_agenticai-langgraph-llm-activity-7423519080160063488-S3m7?utm_source=share&utm_medium=member_desktop&rcm=ACoAADJXJ4UBRMwDhXzF_uqBlAlUrqWoHLgjgCE)

🛠 Setup (uv + pyproject.toml)
1️⃣ Clone the repository
git clone https://github.com/Krishna-Soni-Git/ai-travel-planner.git
cd ai-travel-planner

2️⃣ Install dependencies
uv sync

3️⃣ Create a .env file (not committed)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
GOOGLE_MAPS_API_KEY=your_google_maps_key
BAD_AQI_THRESHOLD=100

4️⃣ Run the application
uv run streamlit run app.py

🔐 Security Notes

API keys are stored in a .env file

.env is ignored via .gitignore

GitHub Push Protection is enabled to prevent secret leaks

📌 Project Highlights

This project demonstrates:

Agentic AI design with tool calling (no hallucinated data)

Multi-API orchestration in a single workflow

Clean separation of concerns (UI, agent, tools, formatting)

Business-ready output formatting

Production-style dependency management with uv

👤 Author

Krishna Soni
AI · Analytics · Agentic Systems · Business Analytics
📍 Halifax, Canada
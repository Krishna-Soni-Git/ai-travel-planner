# app.py
import json
import logging
import re
from datetime import datetime

import streamlit as st
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage

from src.parsing import parse_trip_text
from src.planner import build_agent_request, build_city_explorer_request
from src.agent.single_agent import create_agent_executor
from src.export.pdf_export import build_itinerary_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("travel_agent")

st.set_page_config(page_title="Travel Planner", page_icon="🛫")
st.title("🌍 Travel Planner")

# -----------------------------
# Session State
# -----------------------------
st.session_state.setdefault("history", InMemoryChatMessageHistory())
st.session_state.setdefault("agent", create_agent_executor())

st.session_state.setdefault("last_plan_json", None)
st.session_state.setdefault("last_plan_text", "")
st.session_state.setdefault("last_pdf_bytes", b"")
st.session_state.setdefault("client_name", "")

st.session_state.setdefault("last_generated_local", "")
st.session_state.setdefault("last_generated_iso", "")

# -----------------------------
# Helpers
# -----------------------------
def _now_local_and_iso():
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%d %H:%M"), now.isoformat(timespec="seconds")


def _extract_final_text_from_langgraph_result(result) -> str:
    msgs = (result or {}).get("messages") or []
    if not msgs:
        return ""
    last = msgs[-1]
    return getattr(last, "content", "") or ""


def _invoke_agent(user_text: str) -> str:
    result = st.session_state.agent.invoke({"messages": [HumanMessage(content=user_text)]})
    raw_output = _extract_final_text_from_langgraph_result(result)

    # Print debug in terminal only (NOT in Streamlit UI)
    logger.info("=== Agent raw output start ===\n%s\n=== Agent raw output end ===", raw_output)
    return raw_output


def _build_pdf(title: str, content: str):
    st.session_state.last_pdf_bytes = build_itinerary_pdf(
        title=title,
        client_name=st.session_state.client_name,
        content=content,
    )


def _safe_str(x, default="N/A"):
    s = (x if x is not None else "").strip() if isinstance(x, str) else x
    return s if s else default


# -----------------------------
# Formatting
# -----------------------------
def format_multi_city_report(plan: dict, generated_local: str, generated_iso: str) -> str:
    out = []
    out.append("Travel Planner — Itinerary")
    out.append(f"Generated: {generated_local}")
    out.append("TRAVEL ITINERARY REPORT")
    out.append("=" * 72)

    if st.session_state.client_name:
        out.append(f"Prepared for: {st.session_state.client_name}")
    out.append(f"Generated at: {generated_local}")
    out.append(f"Scope: {_safe_str(plan.get('scope'))}")
    out.append("")

    out.append("EXECUTIVE SUMMARY")
    out.append("-" * 72)
    out.append(_safe_str(plan.get("executive_summary"), ""))
    out.append("")

    for c in (plan.get("cities") or []):
        city = _safe_str(c.get("city"), "Unknown City")
        date = _safe_str(c.get("date"), "Unknown Date")

        out.append("=" * 72)
        out.append(f"{city} — {date}")
        out.append("=" * 72)

        insights = c.get("insights") or {}
        out.append("Conditions & Guidance")
        out.append("-" * 72)
        out.append(f"Weather: {_safe_str(insights.get('weather'))}")
        out.append(f"Umbrella: {_safe_str(insights.get('umbrella'))}")
        out.append(f"Air Quality: {_safe_str(insights.get('air_quality'))}")
        out.append("")

        out.append("Schedule")
        out.append("-" * 72)
        sched = c.get("schedule") or []
        if not sched:
            out.append("No scheduled activities provided.")
        else:
            for s in sched:
                start = _safe_str(s.get("start"), "")
                end = _safe_str(s.get("end"), "")
                activity = _safe_str(s.get("activity"), "")
                address = _safe_str(s.get("address"), "")
                time_range = f"{start}–{end}".strip("–")
                out.append(f"{time_range} | {activity}")
                if address and address != "N/A":
                    out.append(f" Address: {address}")
        out.append("")

        packing = c.get("packing") or []
        if packing:
            out.append("Packing Checklist")
            out.append("-" * 72)
            for item in packing:
                out.append(f"- {str(item).strip()}")
            out.append("")

    return "\n".join(out)


def format_city_explorer_report(plan: dict, generated_local: str, generated_iso: str) -> str:
    # expected schema from build_city_explorer_request
    city = _safe_str(plan.get("city"), "City")
    date = _safe_str(plan.get("date"), "")
    summary = _safe_str(plan.get("summary"), "")
    weather = _safe_str(plan.get("weather"), "")
    air = _safe_str(plan.get("air_quality"), "")

    out = []
    out.append("Travel Planner — City Explorer")
    out.append(f"Generated: {generated_local}")
    out.append("CITY VISIT PLAN")
    out.append("=" * 72)

    if st.session_state.client_name:
        out.append(f"Prepared for: {st.session_state.client_name}")
    out.append(f"Generated at: {generated_iso}")
    out.append(f"Destination: {city}" + (f" — {date}" if date and date != "N/A" else ""))
    out.append("")

    out.append("SUMMARY")
    out.append("-" * 72)
    out.append(summary)
    out.append("")

    out.append("Conditions & Guidance")
    out.append("-" * 72)
    out.append(f"Weather: {weather}")
    out.append(f"Air Quality: {air}")
    out.append("")

    out.append("Suggested Schedule")
    out.append("-" * 72)
    sched = plan.get("schedule") or []
    if not sched:
        out.append("No schedule was generated.")
    else:
        for s in sched:
            start = _safe_str(s.get("start"), "")
            end = _safe_str(s.get("end"), "")
            activity = _safe_str(s.get("activity"), "")
            address = _safe_str(s.get("address"), "")
            time_range = f"{start}–{end}".strip("–")
            out.append(f"{time_range} | {activity}")
            if address and address != "N/A":
                out.append(f" Address: {address}")
    out.append("")

    tips = plan.get("tips") or []
    if tips:
        out.append("Practical Tips")
        out.append("-" * 72)
        for t in tips:
            out.append(f"- {str(t).strip()}")
        out.append("")

    packing = plan.get("packing") or []
    if packing:
        out.append("Packing Checklist")
        out.append("-" * 72)
        for item in packing:
            out.append(f"- {str(item).strip()}")
        out.append("")

    return "\n".join(out)


def render_report_block(text: str):
    st.text(text)


# -----------------------------
# City Explorer input parsing
# -----------------------------
_CITY_HEADER_RE = re.compile(r"^\s*City\s*:\s*(.+?)\s+(\d{4}-\d{2}-\d{2})\s*$", re.IGNORECASE)
_SIMPLE_HEADER_RE = re.compile(r"^\s*(.+?)\s+(\d{4}-\d{2}-\d{2})\s*$")

def parse_city_explorer_box(raw: str):
    """
    One box behavior:
    - First non-empty line must contain "City: Toronto 2026-02-01" OR "Toronto 2026-02-01"
    - Optional following lines: activities like "CN Tower;09:00-11:00" or just "CN Tower"
    Returns: (city, date, has_activities, normalized_trip_text_for_parse_trip_text)
    """
    lines = [ln.strip() for ln in (raw or "").splitlines() if ln.strip()]
    if not lines:
        raise ValueError("Please enter at least: City and Date (e.g., Toronto 2026-02-01).")

    head = lines[0]
    city = ""
    date = ""

    m = _CITY_HEADER_RE.match(head)
    if m:
        city, date = m.group(1).strip(), m.group(2).strip()
    else:
        m2 = _SIMPLE_HEADER_RE.match(head)
        if not m2:
            raise ValueError("First line must look like: Toronto 2026-02-01 (or: City: Toronto 2026-02-01).")
        city, date = m2.group(1).strip(), m2.group(2).strip()

    activity_lines = lines[1:]
    has_activities = len(activity_lines) > 0

    # Build a mini "Trip Input" format that your existing parser understands:
    # City1: <City> <Date>
    normalized = [f"City1: {city} {date}"]
    normalized.extend(activity_lines)
    return city, date, has_activities, "\n".join(normalized)


# -----------------------------
# Run generation
# -----------------------------
def run_generation(prompt_text: str, mode: str):
    local_str, iso_str = _now_local_and_iso()
    st.session_state.last_generated_local = local_str
    st.session_state.last_generated_iso = iso_str

    with st.spinner("Planning..."):
        raw_output = _invoke_agent(prompt_text)

    try:
        plan = json.loads(raw_output)
    except Exception:
        plan = None

    if not isinstance(plan, dict):
        st.session_state.last_plan_json = None
        st.session_state.last_plan_text = raw_output or "No response received from agent."
        st.session_state.last_pdf_bytes = b""
        return

    # Normalize generated_at/client_name
    plan["generated_at"] = iso_str
    plan["client_name"] = st.session_state.client_name or plan.get("client_name", "")

    st.session_state.last_plan_json = plan

    if mode == "City Explorer":
        report = format_city_explorer_report(plan, local_str, iso_str)
        st.session_state.last_plan_text = report
        _build_pdf("Travel Planner — City Explorer", report)
    else:
        report = format_multi_city_report(plan, local_str, iso_str)
        st.session_state.last_plan_text = report
        _build_pdf("Travel Planner — Itinerary", report)


def run_update(change_request: str, mode: str):
    """
    Interactive updates: user can request changes and we send the current JSON for editing.
    """
    if not st.session_state.last_plan_json:
        st.warning("Generate a plan first.")
        return

    current_json = json.dumps(st.session_state.last_plan_json, ensure_ascii=False)

    prompt = (
        "Update the existing plan based on the user request.\n"
        "Return ONLY valid JSON in the SAME schema as the current plan.\n"
        "Keep everything else consistent.\n\n"
        f"CURRENT JSON:\n{current_json}\n\n"
        f"USER REQUEST:\n{change_request}\n"
    )

    run_generation(prompt, mode)


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("Client")
    st.session_state.client_name = st.text_input(
        "Client name",
        value=st.session_state.client_name
    )

    st.divider()
    mode = st.radio("Mode", ["Trip Planner", "City Explorer"], index=0)

    st.divider()

    # Initialize these so they exist for the main logic below
    raw_trip = ""
    raw_city = ""
    interests = ""
    pace = "moderate"
    start_time = "09:00"
    run_trip_btn = False
    run_city_btn = False

    if mode == "Trip Planner":
        st.subheader("Trip Input")
        raw_trip = st.text_area(
            "Format: CityN: Name YYYY-MM-DD and activities",
            height=260,
            placeholder=(
                "City1:\n"
                "\n"
                "\n"
                "City2:\n"
                "\n"
                "\n"
                "City3:\n"
            ),
        )
        run_trip_btn = st.button("Generate Plan", use_container_width=True)

    else:
        st.subheader("City Explorer")
        raw_city = st.text_area(
            "City Explorer input (one box)",
            height=220,
            placeholder=(
                "Toronto 2026-02-01\n"
                "# Optional: add activities below\n"
                "CN Tower;09:00-11:00\n"
            ),
        )

        interests = st.text_input(
            "Optional interests (e.g., museums, food, shopping)",
            value="",
        )

        pace = st.selectbox("Pace", ["slow", "moderate", "fast"], index=1)

        start_time = st.text_input("Start time (HH:MM)", value="09:00")

        run_city_btn = st.button("Create City Day Plan", use_container_width=True)


# -----------------------------
# Run based on mode
# -----------------------------
if mode == "Trip Planner" and run_trip_btn:
    if raw_trip.strip():
        try:
            stops = parse_trip_text(raw_trip)
            prompt_text = build_agent_request(stops, client_name=st.session_state.client_name)
            run_generation(prompt_text, mode="Trip Planner")
        except Exception as e:
            st.error(f"Input parsing error: {e}")
    else:
        st.warning("Please paste trip input first.")

if mode == "City Explorer" and run_city_btn:
    if raw_city.strip():
        try:
            city, date, has_activities, normalized_trip = parse_city_explorer_box(raw_city)

            if has_activities:
                stops = parse_trip_text(normalized_trip)
                prompt_text = build_agent_request(stops, client_name=st.session_state.client_name)
                run_generation(prompt_text, mode="Trip Planner")
            else:
                prompt_text = build_city_explorer_request(
                    city=city,
                    date=date,
                    interests=interests.strip(),
                    start_time=start_time.strip() or "09:00",
                    pace=pace,
                )
                run_generation(prompt_text, mode="City Explorer")

        except Exception as e:
            st.error(f"Input parsing error: {e}")
    else:
        st.warning("Please enter a city and date.")


# -----------------------------
# Main output
# -----------------------------
if st.session_state.last_plan_text:
    st.subheader("Itinerary Report")
    render_report_block(st.session_state.last_plan_text)

    if st.session_state.last_pdf_bytes:
        st.download_button(
            label="📄 Download PDF",
            data=st.session_state.last_pdf_bytes,
            file_name="itinerary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.divider()
    st.subheader("Make Changes")

edit_text = st.text_input(
    "Change request",   
    value="",
    placeholder="",
)
if st.button("Apply Changes", use_container_width=True):
    if edit_text.strip():
        run_update(edit_text.strip(), mode=("City Explorer" if "City Explorer" in st.session_state.last_plan_text else "Trip Planner"))
    else:
        st.warning("Type a change request first.")

else:
    st.info("Use the sidebar to generate a plan.")


# -----------------------------
#  Show small history
# -----------------------------
st.divider()
with st.expander("Conversation history", expanded=False):
    if st.session_state.history.messages:
        for msg in st.session_state.history.messages[-6:]:
            role = "assistant" if msg.type == "ai" else "user"
            with st.chat_message(role):
                st.write(msg.content)
    else:
        st.caption("No follow-ups yet.")

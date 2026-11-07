"""
MeetMind – AI-Powered Meeting Summarizer
Main Streamlit Application Entry Point
"""

import streamlit as st
import json
from pathlib import Path
from config import APP_NAME, APP_TAGLINE
from database import init_db, get_all_meetings, save_meeting
from components import (
    get_custom_css,
    render_sidebar,
    render_dashboard,
    render_upload_view,
    render_history_view,
    render_settings_view
)

# Configure Streamlit page layout and metadata
st.set_page_config(
    page_title=f"{APP_NAME} – AI Meeting Summarizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database tables on app startup
init_db()

# Auto-seed sample meeting on very first run if database is fresh
existing_meetings = get_all_meetings()
if not existing_meetings and "seed_attempted" not in st.session_state:
    st.session_state.seed_attempted = True
    sample_json = Path(__file__).resolve().parent / "sample_data" / "sample_transcript.json"
    if sample_json.exists():
        try:
            with open(sample_json, "r", encoding="utf-8") as f:
                sample_data = json.load(f)
                save_meeting(sample_data)
        except Exception:
            pass

# Initialize session state variables
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_meeting_id" not in st.session_state:
    st.session_state.current_meeting_id = None
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "📊 Dashboard Overview"

# Inject modern SaaS styling
st.markdown(get_custom_css(is_dark_mode=st.session_state.dark_mode), unsafe_allow_html=True)

# Render Sidebar and retrieve active page
selected_page = render_sidebar()

# Page Routing
if selected_page == "📊 Dashboard Overview":
    st.session_state.view_mode = "list"
    render_dashboard()
elif selected_page == "🎙️ Upload & Process Meeting":
    st.session_state.view_mode = "list"
    render_upload_view()
elif selected_page == "🗂️ Meeting History":
    render_history_view()
elif selected_page == "⚙️ Settings & API":
    st.session_state.view_mode = "list"
    render_settings_view()

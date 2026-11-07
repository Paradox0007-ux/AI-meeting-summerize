"""
Settings and Configuration View for MeetMind
Allows users to manage API credentials, select AI models, inspect database status,
and test the end-to-end integration.
"""

import streamlit as st
import os
from pathlib import Path
from config import DB_PATH, DEFAULT_OPENAI_MODEL, SUPPORTED_MODELS, MAX_UPLOAD_SIZE_MB
from database import init_db, save_meeting, get_dashboard_metrics


def render_settings_view():
    """Render settings and administrative panel."""
    st.markdown("""
    <div class="main-header">
        <h1 class="brand-title">Settings & System Configuration</h1>
        <p class="brand-subtitle">Manage OpenAI API credentials, language models, storage, and developer options.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🔑 OpenAI API Credentials")
        current_key = st.session_state.get("user_api_key", os.getenv("OPENAI_API_KEY", ""))

        new_key = st.text_input(
            "OpenAI API Key",
            value=current_key,
            type="password",
            placeholder="sk-proj-...",
            help="Your API key is used exclusively for speech-to-text (Whisper) and summarization (GPT)."
        )

        if st.button("Save API Key", type="primary"):
            st.session_state.user_api_key = new_key.strip()
            st.success("API Key updated for this session!")
            st.rerun()

        st.markdown("""
        <div style="font-size: 0.85rem; color: #64748B; margin-top: 10px;">
            Don't have an API key? You can get one at <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>.
            Alternatively, MeetMind includes a rich Demo Mode that allows exploring all features without an API key.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 🧠 AI Model Selection")
        selected_model = st.selectbox(
            "Default Summarization Model",
            options=SUPPORTED_MODELS,
            index=SUPPORTED_MODELS.index(st.session_state.get("selected_model", DEFAULT_OPENAI_MODEL)) if st.session_state.get("selected_model", DEFAULT_OPENAI_MODEL) in SUPPORTED_MODELS else 0,
            help="Select the model for meeting summarization, decision extraction, and action items."
        )
        st.session_state.selected_model = selected_model

    with col2:
        st.markdown("### 💾 Storage & Database Status")
        db_file = Path(DB_PATH)
        db_exists = db_file.exists()
        db_size_kb = round(db_file.stat().st_size / 1024, 1) if db_exists else 0.0

        metrics = get_dashboard_metrics()

        st.markdown(f"""
        <div class="saas-card">
            <b>Database Engine:</b> SQLite 3<br/>
            <b>Path:</b> <code>{db_file.name}</code><br/>
            <b>Database Size:</b> {db_size_kb} KB<br/>
            <b>Total Meetings:</b> {metrics['total_meetings']}<br/>
            <b>Total Action Items:</b> {metrics['total_action_items']}<br/>
            <b>Max Upload Limit:</b> {MAX_UPLOAD_SIZE_MB} MB
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🛠️ Developer & Testing Actions")
        c_seed, c_reset = st.columns(2)

        with c_seed:
            if st.button("🧪 Seed Sample Meeting", use_container_width=True):
                import json
                sample_path = Path(__file__).resolve().parent.parent / "sample_data" / "sample_transcript.json"
                if sample_path.exists():
                    with open(sample_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        new_id = save_meeting(data)
                        st.success(f"Sample meeting loaded! (ID: {new_id})")
                        st.session_state.current_meeting_id = new_id
                        st.session_state.view_mode = "detail"
                        st.session_state.active_nav = "🗂️ Meeting History"
                        st.rerun()

        with c_reset:
            if st.button("⚠️ Reset Database", use_container_width=True):
                if db_file.exists():
                    import sqlite3
                    conn = sqlite3.connect(str(db_file))
                    c = conn.cursor()
                    c.execute("DROP TABLE IF EXISTS action_items")
                    c.execute("DROP TABLE IF EXISTS decisions")
                    c.execute("DROP TABLE IF EXISTS key_points")
                    c.execute("DROP TABLE IF EXISTS transcripts")
                    c.execute("DROP TABLE IF EXISTS meetings")
                    conn.commit()
                    conn.close()
                    init_db()
                    st.success("Database has been reset.")
                    st.rerun()

"""
Sidebar Component for MeetMind
Handles branding, navigation routing, API key configuration, and theme toggling.
"""

import streamlit as st
import os
from config import APP_NAME, APP_TAGLINE, APP_VERSION, DEFAULT_OPENAI_API_KEY, SUPPORTED_MODELS


def render_sidebar() -> str:
    """
    Render application sidebar and return selected navigation menu item.
    """
    with st.sidebar:
        # Branding Header
        st.markdown(f"""
        <div style="padding: 12px 0 20px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 2rem;">🧠</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.4rem; font-weight: 800; letter-spacing: -0.02em;">
                        {APP_NAME}
                    </h2>
                    <p style="margin: 0; font-size: 0.78rem; color: #64748B;">v{APP_VERSION} • AI Intelligence</p>
                </div>
            </div>
            <p style="margin-top: 8px; font-size: 0.82rem; color: #64748B; line-height: 1.3;">
                {APP_TAGLINE}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation Menu
        nav_options = [
            "📊 Dashboard Overview",
            "🎙️ Upload & Process Meeting",
            "🗂️ Meeting History",
            "⚙️ Settings & API"
        ]

        # Use session state to allow programmatic navigation
        default_idx = 0
        if "active_nav" in st.session_state and st.session_state.active_nav in nav_options:
            default_idx = nav_options.index(st.session_state.active_nav)

        selected_page = st.radio(
            "Navigation",
            options=nav_options,
            index=default_idx,
            label_visibility="collapsed"
        )
        st.session_state.active_nav = selected_page

        st.markdown("---")

        # API Key Status & Configuration
        st.markdown("### 🔑 API Configuration")
        env_key = os.getenv("OPENAI_API_KEY", "") or DEFAULT_OPENAI_API_KEY

        # Initialize session state for user-provided key
        if "user_api_key" not in st.session_state:
            st.session_state.user_api_key = env_key

        effective_key = st.session_state.user_api_key

        if effective_key:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 6px; margin-bottom: 10px;">
                <span style="color: #059669; font-size: 0.9rem;">●</span>
                <span style="color: #065F46; font-size: 0.8rem; font-weight: 600;">OpenAI Key Connected</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: #FEF3C7; border: 1px solid #FDE68A; border-radius: 6px; margin-bottom: 10px;">
                <span style="color: #D97706; font-size: 0.9rem;">●</span>
                <span style="color: #92400E; font-size: 0.8rem; font-weight: 600;">Demo / Sample Mode</span>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("Configure API Key", expanded=not bool(effective_key)):
            custom_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.user_api_key,
                type="password",
                help="Enter your OpenAI API key for Whisper and GPT. It stays strictly in your local session.",
                placeholder="sk-proj-..."
            )
            if custom_key != st.session_state.user_api_key:
                st.session_state.user_api_key = custom_key
                st.rerun()

            selected_model = st.selectbox(
                "LLM Model",
                options=SUPPORTED_MODELS,
                index=0,
                help="Select model for summarization and action extraction."
            )
            st.session_state.selected_model = selected_model

        st.markdown("---")

        # Theme & Display Mode
        st.markdown("### 🎨 Preferences")
        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = False

        dark_mode_toggle = st.checkbox("Dark Theme Mode", value=st.session_state.dark_mode)
        if dark_mode_toggle != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode_toggle
            st.rerun()

        # Footer info
        st.markdown("""
        <div style="margin-top: 30px; font-size: 0.75rem; color: #94A3B8; text-align: center;">
            MeetMind AI • Zero-Hallucination Engine<br/>
            Supports MP3, WAV, M4A, MP4
        </div>
        """, unsafe_allow_html=True)

    return selected_page

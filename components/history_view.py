"""
Meeting History View for MeetMind
Lists past processed meetings, provides quick filtering, and routes into detailed reports.
"""

import streamlit as st
from database import get_all_meetings, delete_meeting
from components.detail_view import render_detail_view


def render_history_view():
    """Render list of past meetings or drill down into specific meeting detail."""
    # Check if a specific meeting is selected for detailed inspection
    if st.session_state.get("view_mode") == "detail" and st.session_state.get("current_meeting_id"):
        render_detail_view(st.session_state.current_meeting_id)
        return

    st.markdown("""
    <div class="main-header">
        <h1 class="brand-title">Meeting History & Archives</h1>
        <p class="brand-subtitle">Search, inspect, and export intelligence from all processed team meetings.</p>
    </div>
    """, unsafe_allow_html=True)

    meetings = get_all_meetings()

    if not meetings:
        st.markdown("""
        <div class="saas-card" style="text-align: center; padding: 48px 20px;">
            <span style="font-size: 3rem;">🗂️</span>
            <h3 style="margin-top: 12px; font-weight: 700;">No Meetings in Database</h3>
            <p style="color: #64748B; max-width: 480px; margin: 0 auto 20px auto;">
                You haven't processed any meetings yet. Upload an audio recording to generate your first meeting report.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎙️ Upload Meeting Audio", type="primary"):
            st.session_state.active_nav = "🎙️ Upload & Process Meeting"
            st.rerun()
        return

    # Search & Filter bar
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("🔍 Search Meetings", placeholder="Search by title or topic...", label_visibility="collapsed")
    with search_col2:
        st.markdown(f"<div style='text-align: right; color: #64748B; padding-top: 8px;'><b>{len(meetings)}</b> total records</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Filter meetings by query
    filtered = [
        m for m in meetings
        if not search_query or search_query.lower() in m["title"].lower() or search_query.lower() in (m.get("overview") or "").lower()
    ]

    if not filtered:
        st.info(f"No meetings matching '{search_query}'.")
        return

    # Render each meeting card
    for m in filtered:
        duration_sec = m.get("audio_duration_seconds", 0)
        dur_str = f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s" if duration_sec else "N/A"
        date_str = m.get("created_at", "")[:16]

        col_main, col_btn = st.columns([5, 2])

        with col_main:
            st.markdown(f"""
            <div style="background: rgba(150, 150, 150, 0.05); border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid #2563EB;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #1E293B;">
                    {m['title']}
                </div>
                <div style="font-size: 0.85rem; color: #64748B; margin-top: 4px; line-height: 1.4;">
                    {m.get('overview', 'No summary available.')[:180]}...
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                    <span class="badge badge-low">📅 {date_str}</span>
                    <span class="badge badge-low">⏱️ {dur_str}</span>
                    <span class="badge badge-done">⚡ {m.get('decisions_count', 0)} decisions</span>
                    <span class="badge badge-med">🎯 {m.get('action_items_count', 0)} action items</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_btn:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button("View Full Report →", key=f"hist_open_{m['id']}", use_container_width=True, type="primary"):
                st.session_state.current_meeting_id = m["id"]
                st.session_state.view_mode = "detail"
                st.rerun()

            if st.button("🗑️ Delete", key=f"hist_del_{m['id']}", use_container_width=True):
                delete_meeting(m["id"])
                st.success(f"Meeting #{m['id']} deleted.")
                st.rerun()

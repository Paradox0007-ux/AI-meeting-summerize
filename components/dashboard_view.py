"""
Dashboard Overview View for MeetMind
Presents aggregate metrics, interactive Plotly analytics, and quick links to recent meeting reports.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import get_dashboard_metrics, get_all_meetings


def render_dashboard():
    """Render main SaaS dashboard overview."""
    st.markdown("""
    <div class="main-header">
        <h1 class="brand-title">Executive Meeting Intelligence</h1>
        <p class="brand-subtitle">Real-time overview of meeting activity, extracted deliverables, and organizational decisions.</p>
    </div>
    """, unsafe_allow_html=True)

    metrics = get_dashboard_metrics()
    all_meetings = get_all_meetings()

    # Metric Cards Row
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{metrics['total_meetings']}</div>
            <div class="metric-lbl">Total Meetings</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col2:
        st.markdown(f"""
        <div class="metric-card warning">
            <div class="metric-val">{metrics['total_action_items']}</div>
            <div class="metric-lbl">Action Items</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col3:
        st.markdown(f"""
        <div class="metric-card success">
            <div class="metric-val">{metrics['completed_actions']}</div>
            <div class="metric-lbl">Tasks Completed</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col4:
        st.markdown(f"""
        <div class="metric-card purple">
            <div class="metric-val">{metrics['total_decisions']}</div>
            <div class="metric-lbl">Decisions Logged</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{metrics['total_duration_minutes']}m</div>
            <div class="metric-lbl">Audio Processed</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Empty State check
    if not all_meetings:
        st.markdown("""
        <div class="saas-card" style="text-align: center; padding: 48px 20px;">
            <span style="font-size: 3rem;">🎙️</span>
            <h3 style="margin-top: 12px; font-weight: 700;">No Meetings Recorded Yet</h3>
            <p style="color: #64748B; max-width: 500px; margin: 0 auto 20px auto;">
                Upload your first audio recording or try our pre-packaged sample meeting to experience AI-powered transcription, diarization, and executive summaries.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("🚀 Upload Meeting Recording", type="primary", use_container_width=True):
                st.session_state.active_nav = "🎙️ Upload & Process Meeting"
                st.rerun()
        with col_btn2:
            if st.button("🧪 Load Sample Meeting", use_container_width=True):
                # Auto seed sample meeting
                from database import save_meeting
                import json
                from pathlib import Path
                sample_path = Path(__file__).resolve().parent.parent / "sample_data" / "sample_transcript.json"
                if sample_path.exists():
                    with open(sample_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        new_id = save_meeting(data)
                        st.session_state.current_meeting_id = new_id
                        st.session_state.view_mode = "detail"
                        st.session_state.active_nav = "🗂️ Meeting History"
                        st.rerun()
        return

    # Interactive Analytics Charts Row
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### 🎯 Action Items by Priority")
        priority_data = metrics.get("priority_distribution", {})
        priorities = ["High", "Medium", "Low"]
        counts = [priority_data.get(p, 0) for p in priorities]
        color_map = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#3B82F6"}

        if sum(counts) > 0:
            fig_p = go.Figure(data=[go.Pie(
                labels=priorities,
                values=counts,
                hole=0.55,
                marker=dict(colors=[color_map[p] for p in priorities]),
                textinfo='label+value',
                hoverinfo='label+percent'
            )])
            fig_p.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.info("No action items available to plot.")

    with chart_col2:
        st.markdown("### 📊 Deliverable Status Breakdown")
        status_data = metrics.get("status_distribution", {})
        statuses = ["Completed", "In Progress", "Pending"]
        status_counts = [status_data.get(s, 0) for s in statuses]
        status_colors = ["#10B981", "#3B82F6", "#94A3B8"]

        if sum(status_counts) > 0:
            fig_s = go.Figure(data=[go.Bar(
                x=statuses,
                y=status_counts,
                marker=dict(color=status_colors, cornerradius=6),
                text=status_counts,
                textposition='auto',
            )])
            fig_s.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                xaxis=dict(title="", showgrid=False),
                yaxis=dict(title="Count", showgrid=True, gridcolor="rgba(150,150,150,0.1)"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("No status data available.")

    st.markdown("---")

    # Recent Meetings Section
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown("### 🗂️ Recent Meetings")
    with h_col2:
        if st.button("+ New Meeting", type="primary", use_container_width=True):
            st.session_state.active_nav = "🎙️ Upload & Process Meeting"
            st.rerun()

    for meeting in all_meetings[:5]:
        duration_sec = meeting.get("audio_duration_seconds", 0)
        dur_str = f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s" if duration_sec else "N/A"
        date_str = meeting.get("created_at", "")[:16]

        col_info, col_action = st.columns([4, 1])
        with col_info:
            st.markdown(f"""
            <div style="padding: 10px 14px; background: rgba(150, 150, 150, 0.05); border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #2563EB;">
                <div style="font-weight: 700; font-size: 1rem; color: #1E293B;">
                    {meeting['title']}
                </div>
                <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                    📅 {date_str} &nbsp;|&nbsp; ⏱️ {dur_str} &nbsp;|&nbsp; 
                    ⚡ {meeting.get('decisions_count', 0)} decisions &nbsp;|&nbsp; 
                    🎯 {meeting.get('action_items_count', 0)} action items
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_action:
            if st.button("Open Report →", key=f"dash_open_{meeting['id']}", use_container_width=True):
                st.session_state.current_meeting_id = meeting["id"]
                st.session_state.view_mode = "detail"
                st.session_state.active_nav = "🗂️ Meeting History"
                st.rerun()

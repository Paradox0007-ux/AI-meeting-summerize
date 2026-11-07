"""
Detailed Meeting Report View for MeetMind
Presents executive summaries, decisions, interactive action item tables,
speaker-diarized transcripts, and multi-format exports (PDF, CSV, TXT, Clipboard).
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
from database import (
    get_meeting_details,
    update_action_item_status,
    add_action_item,
    delete_action_item,
    delete_meeting
)
from services import (
    generate_pdf_report,
    generate_action_items_csv,
    generate_transcript_txt,
    generate_markdown_summary,
    ask_meeting_copilot
)
from config import UPLOADS_DIR, SAMPLE_DIR


def render_detail_view(meeting_id: int):
    """Render the full executive report and interactive workspace for a meeting."""
    meeting = get_meeting_details(meeting_id)

    if not meeting:
        st.error("Meeting report not found.")
        if st.button("← Back to History"):
            st.session_state.view_mode = "list"
            st.rerun()
        return

    # Top Navigation Row
    top_col1, top_col2 = st.columns([4, 2])
    with top_col1:
        if st.button("← Back to All Meetings", key="back_to_list"):
            st.session_state.view_mode = "list"
            st.rerun()
    with top_col2:
        del_confirm = st.checkbox("Confirm Delete", key=f"confirm_del_{meeting_id}")
        if del_confirm:
            if st.button("🗑️ Delete Meeting", type="secondary"):
                delete_meeting(meeting_id)
                st.session_state.view_mode = "list"
                st.success("Meeting deleted.")
                st.rerun()

    # Meeting Header
    duration_sec = meeting.get("audio_duration_seconds", 0)
    dur_str = f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s" if duration_sec else "N/A"
    lang_str = meeting.get("language", "en").upper()
    date_str = meeting.get("created_at", "")[:16]
    filename = meeting.get("audio_filename", "Audio Recording")

    st.markdown(f"""
    <div class="main-header" style="margin-top: 10px;">
        <h1 class="brand-title" style="font-size: 2rem;">{meeting['title']}</h1>
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px;">
            <span class="badge badge-low">📅 {date_str}</span>
            <span class="badge badge-low">⏱️ {dur_str}</span>
            <span class="badge badge-low">🌐 {lang_str}</span>
            <span class="badge badge-low">📁 {filename}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Audio Playback section
    audio_path = UPLOADS_DIR / filename
    if not audio_path.exists():
        # Check in sample_dir
        audio_path = SAMPLE_DIR / filename

    if audio_path.exists():
        with st.expander("▶️ Audio Recording Playback", expanded=False):
            with open(audio_path, "rb") as af:
                st.audio(af.read())

    # Export Action Buttons Bar
    exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)

    # 1. PDF Export
    with exp_col1:
        pdf_bytes = generate_pdf_report(meeting)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"{meeting['title'].lower().replace(' ', '_')}_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # 2. Action Items CSV
    with exp_col2:
        csv_data = generate_action_items_csv(meeting.get("action_items", []))
        st.download_button(
            label="📊 Export Actions (CSV)",
            data=csv_data,
            file_name=f"{meeting['title'].lower().replace(' ', '_')}_actions.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 3. Plain Text Transcript
    with exp_col3:
        txt_data = generate_transcript_txt(meeting)
        st.download_button(
            label="📝 Export Transcript (TXT)",
            data=txt_data,
            file_name=f"{meeting['title'].lower().replace(' ', '_')}_transcript.txt",
            mime="text/plain",
            use_container_width=True
        )

    # 4. Copy Markdown
    with exp_col4:
        md_text = generate_markdown_summary(meeting)
        with st.popover("📋 Copy Summary"):
            st.markdown("Select and copy markdown report:")
            st.code(md_text, language="markdown")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Main Report Tabs
    tab_summary, tab_decisions, tab_actions, tab_transcript, tab_qa = st.tabs([
        "📑 Executive Summary",
        "⚡ Decisions & Agreements",
        "🎯 Action Items & Deliverables",
        "👥 Diarized Transcript",
        "💬 Ask AI Copilot"
    ])

    # TAB 1: EXECUTIVE SUMMARY
    with tab_summary:
        st.markdown("### 📌 Executive Overview")
        st.markdown(f"""
        <div class="saas-card" style="border-left: 4px solid #2563EB;">
            <p style="font-size: 1.05rem; font-weight: 500; color: #1E293B; margin: 0; line-height: 1.6;">
                {meeting.get('overview') or meeting.get('executive_summary')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        if meeting.get("detailed_summary"):
            st.markdown("### 📖 Detailed Discussion Summary")
            st.markdown(f"""
            <div class="saas-card">
                <p style="font-size: 0.95rem; line-height: 1.7; color: #334155; margin: 0;">
                    {meeting['detailed_summary']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Key Points
        points = meeting.get("key_discussion_points", [])
        if points:
            st.markdown("### 💡 Key Discussion Points")
            for kp in points:
                topic = kp.get("topic", "")
                p_text = kp.get("point_text", "")
                st.markdown(f"""
                <div style="padding: 10px 14px; background: rgba(150,150,150,0.05); border-radius: 8px; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #2563EB;">{topic}</span>
                    <p style="margin: 4px 0 0 0; font-size: 0.92rem; color: #334155;">{p_text}</p>
                </div>
                """, unsafe_allow_html=True)

        # Unresolved Questions & Next Steps
        q_col, s_col = st.columns(2)
        with q_col:
            st.markdown("### ❓ Open Questions")
            questions = meeting.get("unresolved_questions", [])
            if questions:
                for q in questions:
                    st.markdown(f"- ❓ {q}")
            else:
                st.markdown("<p style='color: #94A3B8;'>No unresolved questions recorded.</p>", unsafe_allow_html=True)

        with s_col:
            st.markdown("### 🚀 Next Steps")
            next_steps = meeting.get("next_steps", [])
            if next_steps:
                for ns in next_steps:
                    st.markdown(f"- ➡️ {ns}")
            else:
                st.markdown("<p style='color: #94A3B8;'>No next steps recorded.</p>", unsafe_allow_html=True)

    # TAB 2: DECISIONS & AGREEMENTS
    with tab_decisions:
        decisions = meeting.get("decisions", [])
        st.markdown(f"### ⚡ Captured Decisions & Agreements ({len(decisions)})")

        if not decisions:
            st.info("No explicit decisions were identified in this meeting.")
        else:
            for idx, d in enumerate(decisions, start=1):
                topic = d.get("context_topic", "General")
                problem = d.get("problem_discussed", "")
                solution = d.get("proposed_solution", "")
                st.markdown(f"""
                <div class="decision-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="decision-title">#{idx} {d.get('decision_text')}</span>
                        <span class="badge badge-low">{topic}</span>
                    </div>
                    {f'<div class="decision-meta"><b>Problem Discussed:</b> {problem}</div>' if problem else ''}
                    {f'<div class="decision-meta" style="color: #047857;"><b>Agreed Solution:</b> {solution}</div>' if solution else ''}
                </div>
                """, unsafe_allow_html=True)

    # TAB 3: ACTION ITEMS
    with tab_actions:
        action_items = meeting.get("action_items", [])
        st.markdown(f"### 🎯 Trackable Action Items ({len(action_items)})")
        st.caption("Change status directly using the dropdown to keep your team in sync.")

        with st.expander("➕ Add New Action Item", expanded=False):
            with st.form(f"add_action_form_{meeting_id}", clear_on_submit=True):
                col_t, col_a = st.columns([3, 2])
                with col_t:
                    new_task = st.text_input("Task Description *", placeholder="e.g. Prepare API deployment checklist")
                with col_a:
                    new_assignee = st.text_input("Assignee", placeholder="e.g. Sarah Chen (or leave blank)")

                col_d, col_p, col_s = st.columns(3)
                with col_d:
                    new_due = st.text_input("Deadline", placeholder="e.g. Next Friday (or leave blank)")
                with col_p:
                    new_prio = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                with col_s:
                    new_stat = st.selectbox("Status", ["Pending", "In Progress", "Completed"], index=0)

                submit_action = st.form_submit_button("Add Action Item", type="primary")
                if submit_action and new_task.strip():
                    add_action_item(
                        meeting_id=meeting_id,
                        task_description=new_task,
                        assigned_person=new_assignee or "Not specified",
                        deadline=new_due or "Not specified",
                        priority=new_prio,
                        status=new_stat
                    )
                    st.success("Action item added.")
                    st.rerun()

        if not action_items:
            st.info("No action items were assigned during this meeting.")
        else:
            # Header row
            h_task, h_who, h_due, h_prio, h_stat, h_del = st.columns([3.5, 2, 2, 1.5, 2, 1])
            with h_task: st.markdown("**Task Description**")
            with h_who: st.markdown("**Assignee**")
            with h_due: st.markdown("**Deadline**")
            with h_prio: st.markdown("**Priority**")
            with h_stat: st.markdown("**Status**")
            with h_del: st.markdown("**Action**")
            st.markdown("<hr style='margin: 4px 0 12px 0;'/>", unsafe_allow_html=True)

            for item in action_items:
                c_task, c_who, c_due, c_prio, c_stat, c_del = st.columns([3.5, 2, 2, 1.5, 2, 1])
                with c_task:
                    st.markdown(f"**{item.get('task_description')}**")
                with c_who:
                    assignee = item.get("assigned_person", "Not specified")
                    badge_cls = "badge-pending" if assignee == "Not specified" else "badge-low"
                    st.markdown(f"<span class='badge {badge_cls}'>👤 {assignee}</span>", unsafe_allow_html=True)
                with c_due:
                    due = item.get("deadline", "Not specified")
                    st.markdown(f"<span style='font-size: 0.85rem; color: #64748B;'>📅 {due}</span>", unsafe_allow_html=True)
                with c_prio:
                    prio = item.get("priority", "Medium")
                    p_cls = "badge-high" if prio == "High" else "badge-med" if prio == "Medium" else "badge-low"
                    st.markdown(f"<span class='badge {p_cls}'>{prio}</span>", unsafe_allow_html=True)
                with c_stat:
                    current_status = item.get("status", "Pending")
                    statuses = ["Pending", "In Progress", "Completed"]
                    current_idx = statuses.index(current_status) if current_status in statuses else 0
                    new_status = st.selectbox(
                        "Status",
                        options=statuses,
                        index=current_idx,
                        key=f"status_select_{item['id']}",
                        label_visibility="collapsed"
                    )
                    if new_status != current_status:
                        update_action_item_status(item["id"], new_status)
                        st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_item_{item['id']}", help="Delete action item"):
                        delete_action_item(item["id"])
                        st.rerun()

    # TAB 4: TRANSCRIPT & DIARIZATION
    with tab_transcript:
        transcript = meeting.get("transcript", {})
        segments = transcript.get("segments", [])

        st.markdown("### 👥 Speaker Diarized Transcript")

        if segments:
            # Speaker Talk-Time Analytics
            speaker_durations = {}
            speaker_turns_count = {}
            for seg in segments:
                spk = seg.get("speaker", "Speaker")
                dur = max(0.5, seg.get("end", 0.0) - seg.get("start", 0.0))
                speaker_durations[spk] = speaker_durations.get(spk, 0.0) + dur
                speaker_turns_count[spk] = speaker_turns_count.get(spk, 0) + 1

            with st.expander("📊 Speaker Participation & Talk-Time Analytics", expanded=False):
                col_chart, col_stats = st.columns([3, 2])
                with col_chart:
                    fig_spk = go.Figure(data=[go.Pie(
                        labels=list(speaker_durations.keys()),
                        values=[round(v, 1) for v in speaker_durations.values()],
                        hole=0.55,
                        textinfo='label+percent',
                        hoverinfo='label+value'
                    )])
                    fig_spk.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=220,
                        paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False
                    )
                    st.plotly_chart(fig_spk, use_container_width=True)
                with col_stats:
                    st.markdown("**Participation Breakdown:**")
                    for spk, dur in speaker_durations.items():
                        st.markdown(f"- **{spk}:** {int(dur)}s ({speaker_turns_count.get(spk, 0)} conversational turns)")

            # Extract unique speakers
            unique_speakers = sorted(list(set(s.get("speaker", "Speaker") for s in segments)))

            filter_col1, filter_col2 = st.columns([1, 2])
            with filter_col1:
                selected_speaker = st.selectbox(
                    "Filter by Speaker",
                    options=["All Speakers"] + unique_speakers
                )
            with filter_col2:
                search_query = st.text_input("Search Dialogue", placeholder="Filter by keywords...")

            # Render dialogue turns
            displayed_turns = 0
            for seg in segments:
                spk = seg.get("speaker", "Speaker 1")
                if selected_speaker != "All Speakers" and spk != selected_speaker:
                    continue

                text = seg.get("text", "")
                if search_query and search_query.lower() not in text.lower():
                    continue

                displayed_turns += 1
                start_sec = seg.get("start", 0.0)
                end_sec = seg.get("end", 0.0)
                time_str = f"{int(start_sec // 60):02d}:{int(start_sec % 60):02d} - {int(end_sec // 60):02d}:{int(end_sec % 60):02d}"

                # Assign color classes based on speaker ID
                num = spk.split()[-1] if spk.split()[-1].isdigit() else "1"
                spk_cls = f"speaker-{(int(num) % 4) or 4}"

                st.markdown(f"""
                <div class="transcript-line">
                    <div style="display: flex; align-items: center;">
                        <span class="speaker-badge {spk_cls}">🎙️ {spk}</span>
                        <span class="transcript-time">[{time_str}]</span>
                    </div>
                    <div class="transcript-text">{text}</div>
                </div>
                """, unsafe_allow_html=True)

            if displayed_turns == 0:
                st.info("No segments match your filter.")
        else:
            # Full raw text fallback
            full_text = transcript.get("text", "") if isinstance(transcript, dict) else str(transcript)
            st.text_area("Full Transcript", value=full_text, height=400, disabled=True)

    # TAB 5: ASK AI COPILOT
    with tab_qa:
        st.markdown("### 💬 Ask MeetMind AI Copilot")
        st.caption("Ask questions about this meeting. Answers are grounded 100% in the transcript and structured report.")

        qa_session_key = f"chat_history_{meeting_id}"
        if qa_session_key not in st.session_state:
            st.session_state[qa_session_key] = []

        # Display history
        for msg in st.session_state[qa_session_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_query = st.chat_input("Ask a question about this meeting (e.g. 'What was decided about chunking?')...")
        if user_query:
            st.session_state[qa_session_key].append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing transcript..."):
                    api_key = st.session_state.get("user_api_key", None)
                    model = st.session_state.get("selected_model", "gpt-4o-mini")
                    ans = ask_meeting_copilot(meeting, user_query, api_key=api_key, model=model)
                    st.markdown(ans)
                    st.session_state[qa_session_key].append({"role": "assistant", "content": ans})

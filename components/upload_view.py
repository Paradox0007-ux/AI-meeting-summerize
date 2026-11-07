"""
Upload and Process View for MeetMind
Handles audio file upload (MP3, WAV, M4A, MP4), validation, sample audio testing,
and step-by-step AI processing pipeline with live progress indicators.
"""

import streamlit as st
import time
from pathlib import Path
from config import MAX_UPLOAD_SIZE_MB, SUPPORTED_AUDIO_EXTENSIONS
from services import (
    validate_audio_file,
    save_uploaded_audio,
    format_file_size,
    get_audio_duration_seconds,
    get_sample_meeting_audio,
    transcribe_audio_file,
    generate_meeting_summary
)
from database import save_meeting


def render_upload_view():
    """Render upload interface and audio processing pipeline."""
    st.markdown("""
    <div class="main-header">
        <h1 class="brand-title">Upload Meeting Recording</h1>
        <p class="brand-subtitle">Convert conversations into structured summaries, speaker-attributed transcripts, and actionable deliverables.</p>
    </div>
    """, unsafe_allow_html=True)

    # Two column layout: Upload panel and sample/settings panel
    col_upload, col_settings = st.columns([5, 3])

    with col_upload:
        st.markdown("### 🎙️ Audio Input")
        upload_tab, record_tab = st.tabs(["📁 Upload File", "🎤 Record Live"])

        with upload_tab:
            uploaded_file = st.file_uploader(
                "Drop your meeting audio recording here",
                type=[ext.replace(".", "") for ext in SUPPORTED_AUDIO_EXTENSIONS],
                help=f"Supported formats: MP3, WAV, M4A, MP4 (Max {MAX_UPLOAD_SIZE_MB}MB)",
                label_visibility="visible"
            )

        with record_tab:
            recorded_audio = st.audio_input("Record Meeting from Microphone")

        # Sample Audio Shortcut
        st.markdown("<p style='font-size: 0.85rem; color: #64748B; margin-top: 14px;'>Don't have an audio file ready? Try our built-in sample:</p>", unsafe_allow_html=True)
        use_sample = st.button("🧪 Use Pre-Loaded Sample Meeting Audio", use_container_width=True)

    with col_settings:
        st.markdown("### ⚙️ Processing Options")
        meeting_title_input = st.text_input(
            "Meeting Title (Optional)",
            placeholder="e.g. Q3 Architecture & Sprint Review",
            help="Leave blank to let AI automatically generate a title."
        )

        language_options = [
            "Auto Detect", "English (en)", "Spanish (es)", "French (fr)",
            "German (de)", "Japanese (ja)", "Chinese (zh)", "Hindi (hi)"
        ]
        lang_choice = st.selectbox("Audio Language", options=language_options, index=0)
        lang_code = lang_choice.split("(")[-1].replace(")", "").strip() if "(" in lang_choice else None

        additional_notes = st.text_area(
            "Meeting Context / Agenda (Optional)",
            placeholder="Add relevant project context or attendees to guide the AI...",
            height=100
        )

    # Determine file to process
    active_file = None
    is_sample_mode = False

    if use_sample:
        sample_path = get_sample_meeting_audio()
        if sample_path.exists():
            is_sample_mode = True
            st.session_state.sample_active = True
        else:
            st.error("Sample audio file could not be generated.")

    if uploaded_file is not None:
        st.session_state.sample_active = False
        active_file = uploaded_file
    elif recorded_audio is not None:
        st.session_state.sample_active = False
        if not hasattr(recorded_audio, "name") or not recorded_audio.name:
            recorded_audio.name = "microphone_recording.wav"
        active_file = recorded_audio

    # File Preview & Processing Card
    if active_file or st.session_state.get("sample_active"):
        st.markdown("---")
        st.markdown("### 📋 File Verification & Audio Preview")

        if active_file:
            # Validate uploaded file
            is_valid, error_msg = validate_audio_file(active_file)
            if not is_valid:
                st.error(f"❌ {error_msg}")
                return

            file_name = active_file.name
            file_size_str = format_file_size(active_file.size)
            st.success(f"✅ **{file_name}** ready ({file_size_str})")
            st.audio(active_file)
        else:
            sample_path = get_sample_meeting_audio()
            file_name = "sample_meeting.wav"
            file_size_str = format_file_size(sample_path.stat().st_size)
            st.info(f"ℹ️ **Sample Meeting Audio loaded** ({file_size_str})")
            with open(sample_path, "rb") as af:
                st.audio(af.read(), format="audio/wav")

        # Action Button to launch AI pipeline
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("✨ Transcribe & Summarize with MeetMind", type="primary", use_container_width=True):
            run_processing_pipeline(
                uploaded_file=active_file,
                is_sample=st.session_state.get("sample_active", False),
                custom_title=meeting_title_input,
                language=lang_code,
                context_notes=additional_notes
            )


def run_processing_pipeline(uploaded_file, is_sample: bool, custom_title: str, language: str, context_notes: str):
    """Execute the multi-stage AI meeting extraction pipeline with progress feedback."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Save audio file
        status_text.markdown("⏳ **Step 1/5:** Validating and saving audio...")
        progress_bar.progress(15)
        time.sleep(0.3)

        if is_sample:
            saved_path = get_sample_meeting_audio()
            saved_filename = "sample_meeting.wav"
            file_size_bytes = saved_path.stat().st_size
        else:
            saved_filename, saved_path = save_uploaded_audio(uploaded_file)
            file_size_bytes = uploaded_file.size

        duration_sec = get_audio_duration_seconds(saved_path)

        # Step 2: Speech-to-Text Transcription with Whisper
        status_text.markdown("🎙️ **Step 2/5:** Transcribing speech with Whisper API...")
        progress_bar.progress(40)

        api_key = st.session_state.get("user_api_key", None)
        transcription_res = transcribe_audio_file(
            audio_path=saved_path,
            api_key=api_key,
            language=language
        )

        raw_transcript_text = transcription_res.get("text", "")
        detected_lang = transcription_res.get("language", "en")
        segments = transcription_res.get("segments", [])

        # Step 3: Diarization & Speaker Turn Attribution
        status_text.markdown("👥 **Step 3/5:** Segmenting speakers and conversation turns...")
        progress_bar.progress(65)
        time.sleep(0.3)

        # Step 4: AI Summarization & Action Item Extraction
        status_text.markdown("🧠 **Step 4/5:** Extracting executive summary, decisions, and action items...")
        progress_bar.progress(85)

        chosen_model = st.session_state.get("selected_model", "gpt-4o-mini")
        ai_report = generate_meeting_summary(
            transcript_text=raw_transcript_text,
            api_key=api_key,
            model=chosen_model,
            additional_context=context_notes
        )

        final_title = custom_title.strip() if custom_title and custom_title.strip() else ai_report.title

        # Step 5: Save record into SQLite Database
        status_text.markdown("💾 **Step 5/5:** Finalizing report & persisting to database...")
        progress_bar.progress(95)

        meeting_record = {
            "title": final_title,
            "audio_filename": saved_filename,
            "audio_filesize_bytes": file_size_bytes,
            "audio_duration_seconds": duration_sec,
            "language": detected_lang,
            "overview": ai_report.overview,
            "executive_summary": ai_report.executive_summary,
            "detailed_summary": ai_report.detailed_summary,
            "unresolved_questions": ai_report.unresolved_questions,
            "next_steps": ai_report.next_steps,
            "status": "processed",
            "transcript": {
                "text": raw_transcript_text,
                "segments": segments
            },
            "action_items": [item.model_dump() for item in ai_report.action_items],
            "decisions": [dec.model_dump() for dec in ai_report.decisions],
            "key_discussion_points": [kp.model_dump() for kp in ai_report.key_discussion_points]
        }

        meeting_id = save_meeting(meeting_record)
        progress_bar.progress(100)
        status_text.markdown("🎉 **Processing complete!** Opening your report...")
        time.sleep(0.5)

        # Navigate directly to the newly generated meeting details
        st.session_state.current_meeting_id = meeting_id
        st.session_state.view_mode = "detail"
        st.session_state.active_nav = "🗂️ Meeting History"
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Processing Error: {str(e)}")

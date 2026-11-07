# 🧠 MeetMind – AI-Powered Meeting Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20%26%20GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![SQLite](https://img.shields.io/badge/SQLite-Embedded-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Generation-E25A1C?style=for-the-badge)](https://www.reportlab.com)

**MeetMind** is an enterprise-grade, responsive AI application that transforms unstructured meeting audio recordings into structured, actionable intelligence. It automatically generates executive summaries, extracts critical decisions, tracks action items with strict anti-hallucination controls, attributes speaker turns, and exports multi-format executive reports.

---

## 🌟 Key Features

### 1. 🎙️ Comprehensive Audio Processing
- **Multi-Format Support:** Ingests `.mp3`, `.wav`, `.m4a`, and `.mp4` audio files up to 50MB.
- **In-Browser Microphone Recording:** Direct live meeting capture via Streamlit's native `st.audio_input` without third-party plugins.
- **Drag-and-Drop Uploader:** Real-time file validation (format, size, zero-byte protection).
- **Audio Playback:** Built-in interactive audio player to listen to recordings directly within the app.
- **Built-in Sample Audio:** One-click sample audio testing for instant exploration without needing a personal recording.
- **Audio Chunking Engine:** Transparent cumulative splitting for recordings over 24MB to ensure compatibility with Whisper API limits.

### 2. ⚡ Speech-to-Text Transcription & Diarization
- **OpenAI Whisper API (`whisper-1`):** High-fidelity transcription with `verbose_json` segment timestamps (`[MM:SS - MM:SS]`).
- **Speaker Diarization & Attribution:** Chronological conversational turns labeled as `Speaker 1`, `Speaker 2`, etc., without guessing real identities.
- **Speaker Participation Analytics:** Interactive Plotly donut chart displaying talk-time percentages and turn counts per speaker.
- **Multi-Language Support:** Auto-detection with support for English, Spanish, French, German, Japanese, Chinese, Hindi, and more.
- **Interactive Transcript Explorer:** Search through dialogue by keyword and filter turns by specific speaker.

### 3. 🧠 Zero-Hallucination AI Summarization
- **Executive Summary:** High-level narrative designed for C-suite briefings.
- **Detailed Summary:** In-depth thematic breakdown of the entire meeting.
- **Key Discussion Points:** Structured by topics with clear takeaways.
- **Strict Anti-Hallucination Guardrails:** Enforced via Pydantic schema validation. If an action item lacks an explicit assignee or deadline in the conversation, it is strictly recorded as **`Not specified`**—never fabricated.

### 4. 💬 Interactive Meeting AI Copilot
- Grounded conversational Q&A assistant for every meeting.
- Ask questions like *"Who is assigned to the API chunking task?"* or *"What was decided about SQLite?"* and receive concise, speaker-cited responses.

### 5. ⚡ Decision & Problem-Solving Extraction
- Captures explicit decisions, agreements, and consensus reached during the meeting.
- Pairs each decision with the **problem discussed** and the **agreed solution**.

### 6. 🎯 Trackable Action Items & Task Manager
- Extracts actionable tasks with **Assignee**, **Deadline**, **Priority Level** (`High`, `Medium`, `Low`), and **Status** (`Pending`, `In Progress`, `Completed`).
- Interactive dashboard dropdown allows updating task status in real time with SQLite persistence.
- Allows team leads to dynamically append new action items post-meeting.

### 7. 📤 Multi-Format Report Export
- **Executive PDF Report:** Custom ReportLab layout with page numbering, corporate header, executive summary box, and styled tables.
- **Action Items CSV:** Instant Pandas export compatible with Excel, Google Sheets, Jira, and Asana.
- **Plain Text TXT:** Full speaker-diarized transcript with timestamps.
- **Markdown Summary:** One-click copy for Slack, Notion, or email.

### 8. 📊 Modern SaaS Dashboard Design
- **Dark & Light Mode:** Toggleable color themes optimized for readability.
- **Interactive Plotly Visualizations:** Action items by priority (donut chart) and deliverable status breakdown (bar chart).
- **Executive Metrics:** Total meetings analyzed, action items tracked, completion rates, and total audio duration.

---

## 🏗️ Project Architecture

```
AI meeting summerizer/
├── app.py                     # Main Streamlit application entry point
├── config.py                  # Configuration, environment variables, constants
├── requirements.txt           # Python dependencies
├── .env.example               # Template environment variables
├── .env                       # Local environment file (optional)
├── test_meetmind.py           # Automated end-to-end test suite
├── README.md                  # Comprehensive documentation
├── database/
│   ├── __init__.py
│   └── db_manager.py          # SQLite schema, tables, and CRUD operations
├── services/
│   ├── __init__.py
│   ├── audio_service.py       # Audio validation, chunking, and sample generator
│   ├── transcription_service.py # Whisper API, verbose_json timestamps, diarization
│   ├── summarization_service.py # GPT-4o-mini structured extraction & Pydantic validation
│   └── export_service.py      # ReportLab PDF, CSV, TXT, and Markdown exporters
├── components/
│   ├── __init__.py
│   ├── styles.py              # Modern SaaS CSS design system (Dark & Light)
│   ├── sidebar.py             # Navigation, theme toggle, and API key management
│   ├── dashboard_view.py      # Analytics metrics and interactive Plotly charts
│   ├── upload_view.py         # Drag-and-drop upload and 5-stage processing pipeline
│   ├── history_view.py        # Archive table, search, and meeting management
│   ├── detail_view.py         # Full executive report, tabs, and export actions
│   └── settings_view.py       # API configuration and database diagnostics
└── sample_data/
    ├── sample_transcript.json # Pre-recorded realistic multi-speaker sample meeting
    └── sample_meeting.wav     # Valid test audio file for immediate out-of-the-box testing
```

---

## 🚀 Quick Start Guide

### 1. Clone or Open the Repository
```bash
git clone https://github.com/your-username/meetmind.git
cd "AI meeting summerizer"
```

### 2. Set Up a Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your OpenAI API Key
Create a `.env` file from the provided `.env.example`:
```bash
# Windows PowerShell
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Open `.env` and add your OpenAI API Key:
```ini
OPENAI_API_KEY=sk-proj-your_actual_key_here
OPENAI_MODEL=gpt-4o-mini
```
*(Alternatively, you can enter your API key directly inside the app's sidebar during your session without editing files).*

### 5. Launch the Application
```bash
streamlit run app.py
```
The application will automatically open in your default browser at `http://localhost:8501`.

---

## 🧪 Testing

MeetMind includes an automated test suite verifying database integrity, audio handling, ReportLab PDF generation, CSV exports, and anti-hallucination sanitization:

```bash
python test_meetmind.py
```

Expected output:
```text
=== Running MeetMind Comprehensive Tests ===
[1/5] Testing Database Manager...
[2/5] Testing Audio Service...
[3/5] Testing Export Service...
[4/5] Testing Pydantic Anti-Hallucination Schema...
[5/5] Testing Offline/Demo Fallback Engines...
SUCCESS: ALL MEETMIND TESTS PASSED SUCCESSFULLY!
```

---

## 🌐 Running on Replit

MeetMind is designed to run seamlessly on [Replit](https://replit.com):

1. **Import Repository:** Create a new Python Repl and import this project.
2. **Configure Secrets:** Open the **Secrets (Environment Variables)** tab in Replit and add:
   - Key: `OPENAI_API_KEY`
   - Value: `your_openai_api_key`
3. **Configure Run Command:** In your `.replit` configuration:
   ```toml
   run = "streamlit run app.py --server.port 5000 --server.address 0.0.0.0"
   ```
4. **Click Run:** Replit will install the packages from `requirements.txt` and launch the web view automatically.

---

## 🔒 Security & Data Privacy

- **No Hardcoded Keys:** All credentials are kept in `.env` or temporary session memory.
- **Local Persistence:** Meeting transcripts, summaries, and action items are stored locally in an embedded SQLite database (`meetmind.db`).
- **Zero Hallucination:** Action items enforce `"Not specified"` for unstated owners or deadlines.

---

## 📄 License
This project is licensed under the MIT License.

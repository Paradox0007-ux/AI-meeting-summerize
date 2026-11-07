"""
MeetMind Configuration Module
Handles environment variables, constants, paths, and application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR = DATA_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)
SAMPLE_DIR = BASE_DIR / "sample_data"
SAMPLE_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "meetmind.db"))

# OpenAI Settings
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SUPPORTED_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

# File upload constraints
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
SUPPORTED_AUDIO_EXTENSIONS = [".mp3", ".wav", ".m4a", ".mp4"]
SUPPORTED_MIME_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "video/mp4": ".mp4",
    "audio/aac": ".m4a"
}

# App metadata
APP_NAME = "MeetMind"
APP_TAGLINE = "AI-Powered Meeting Summarizer & Action Intelligence"
APP_VERSION = "1.0.0"

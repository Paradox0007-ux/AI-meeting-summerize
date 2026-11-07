"""
Audio Service for MeetMind
Handles audio file validation, saving, metadata extraction, chunking, and sample generation.
"""

import os
import wave
import struct
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from config import UPLOADS_DIR, SAMPLE_DIR, MAX_UPLOAD_SIZE_MB, SUPPORTED_AUDIO_EXTENSIONS


def validate_audio_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate uploaded file format and size constraints.
    Returns (is_valid, error_message).
    """
    if uploaded_file is None:
        return False, "No file provided."

    file_name = uploaded_file.name
    ext = Path(file_name).suffix.lower()

    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Supported formats: {', '.join(SUPPORTED_AUDIO_EXTENSIONS)}"

    file_size_bytes = uploaded_file.size
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if file_size_bytes > max_bytes:
        size_mb = file_size_bytes / (1024 * 1024)
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed size ({MAX_UPLOAD_SIZE_MB} MB)."

    if file_size_bytes == 0:
        return False, "Uploaded file is empty (0 bytes)."

    return True, ""


def format_file_size(size_bytes: int) -> str:
    """Format bytes into readable string (KB, MB)."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def save_uploaded_audio(uploaded_file) -> Tuple[str, Path]:
    """
    Save uploaded file to disk in uploads directory.
    Returns (filename, absolute_path).
    """
    safe_name = Path(uploaded_file.name).name
    # Append unique timestamp prefix to prevent overwrite collisions
    import time
    timestamp_prefix = int(time.time())
    final_name = f"{timestamp_prefix}_{safe_name}"
    save_path = UPLOADS_DIR / final_name

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return final_name, save_path


def get_audio_duration_seconds(file_path: Path) -> float:
    """
    Extract or estimate duration in seconds.
    Supports native WAV inspection; falls back to bitrate estimation if header parsing fails.
    """
    ext = file_path.suffix.lower()
    if ext == ".wav":
        try:
            with wave.open(str(file_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 2)
        except Exception:
            pass

    # Approximate duration based on standard 128kbps meeting audio bitrate
    file_size_bytes = os.path.getsize(file_path)
    estimated_seconds = (file_size_bytes * 8) / (128 * 1000)
    return round(max(estimated_seconds, 1.0), 2)


def get_sample_meeting_audio() -> Path:
    """
    Ensure a valid sample audio file exists in sample_data.
    Generates a realistic synthetic meeting WAV chime sequence if not present.
    """
    sample_wav = SAMPLE_DIR / "sample_meeting.wav"
    if sample_wav.exists() and sample_wav.stat().st_size > 1000:
        return sample_wav

    # Generate a lightweight 6-second valid WAV audio representing 3 speaker turns
    sample_rate = 16000
    duration_secs = 6
    num_frames = sample_rate * duration_secs

    # Frequencies simulating 3 speaker turns (440Hz, 554Hz, 659Hz) with pauses
    with wave.open(str(sample_wav), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(num_frames):
            time_sec = i / float(sample_rate)
            # Speaker 1: 0 - 1.8s (440Hz)
            # Pause: 1.8s - 2.0s
            # Speaker 2: 2.0s - 3.8s (554Hz)
            # Pause: 3.8s - 4.0s
            # Speaker 3: 4.0s - 5.8s (659Hz)
            if 0.0 <= time_sec < 1.8:
                freq = 440.0
                amplitude = 12000 * math.sin(2 * math.pi * freq * time_sec)
            elif 2.0 <= time_sec < 3.8:
                freq = 554.37
                amplitude = 12000 * math.sin(2 * math.pi * freq * time_sec)
            elif 4.0 <= time_sec < 5.8:
                freq = 659.25
                amplitude = 12000 * math.sin(2 * math.pi * freq * time_sec)
            else:
                amplitude = 0.0

            data = struct.pack("<h", int(amplitude))
            wav_file.writeframesraw(data)

    return sample_wav


def split_audio_if_needed(file_path: Path, max_chunk_mb: int = 24) -> List[Path]:
    """
    Check if audio file exceeds Whisper's 25MB limit.
    If it does, split WAV files or yield single file path.
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb <= max_chunk_mb:
        return [file_path]

    # If it's a WAV file, we can split it into chunks
    if file_path.suffix.lower() == ".wav":
        chunks = []
        try:
            with wave.open(str(file_path), "rb") as wf:
                params = wf.getparams()
                framerate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                nchannels = wf.getnchannels()
                total_frames = wf.getnframes()

                bytes_per_second = framerate * sampwidth * nchannels
                chunk_duration_sec = 600  # 10 minutes chunk
                chunk_frames = chunk_duration_sec * framerate

                current_frame = 0
                chunk_idx = 1
                while current_frame < total_frames:
                    frames_to_read = min(chunk_frames, total_frames - current_frame)
                    raw_data = wf.readframes(frames_to_read)

                    chunk_path = file_path.parent / f"{file_path.stem}_part{chunk_idx}.wav"
                    with wave.open(str(chunk_path), "wb") as chunk_wf:
                        chunk_wf.setparams(params)
                        chunk_wf.writeframes(raw_data)

                    chunks.append(chunk_path)
                    current_frame += frames_to_read
                    chunk_idx += 1
            return chunks
        except Exception:
            return [file_path]

    return [file_path]

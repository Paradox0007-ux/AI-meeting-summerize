"""
Transcription Service for MeetMind
Integrates OpenAI Whisper API with verbose_json output, timestamp extraction,
speaker segmenting, and multi-language support.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from openai import OpenAI
from config import DEFAULT_OPENAI_API_KEY
from services.audio_service import split_audio_if_needed, get_audio_duration_seconds


def get_openai_client(api_key: Optional[str] = None) -> Optional[OpenAI]:
    """Instantiate and return OpenAI client with given key or fallback to environment."""
    key = (api_key or os.getenv("OPENAI_API_KEY") or DEFAULT_OPENAI_API_KEY or "").strip()
    if not key:
        return None
    return OpenAI(api_key=key)


def transcribe_audio_file(
    audio_path: Path,
    api_key: Optional[str] = None,
    language: Optional[str] = None,
    prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe audio file using OpenAI Whisper API (`whisper-1`).
    Automatically splits files > 24MB into chunks with cumulative timestamp offsets.
    Requests verbose_json format to retrieve segment-level timestamps.
    Returns:
    {
        "text": full transcript string,
        "language": detected language (e.g. 'en', 'es'),
        "duration": duration in seconds,
        "segments": list of segment dicts [{'id', 'start', 'end', 'text', 'speaker'}]
    }
    """
    client = get_openai_client(api_key)

    if not client:
        # Fallback to local demo transcription for instant out-of-the-box exploration
        return get_fallback_demo_transcript(audio_path)

    try:
        chunks = split_audio_if_needed(audio_path, max_chunk_mb=24)
        all_segments = []
        full_text_parts = []
        cumulative_time = 0.0
        detected_language = "en"
        total_duration = 0.0

        for chunk_idx, chunk_file in enumerate(chunks):
            with open(chunk_file, "rb") as audio_file:
                kwargs = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json"
                }
                if language and language.strip().lower() != "auto":
                    kwargs["language"] = language.strip().lower()
                if prompt:
                    kwargs["prompt"] = prompt

                response = client.audio.transcriptions.create(**kwargs)

            chunk_text = getattr(response, "text", "")
            if chunk_text:
                full_text_parts.append(chunk_text)

            detected_language = getattr(response, "language", detected_language)
            chunk_duration = getattr(response, "duration", get_audio_duration_seconds(chunk_file))
            total_duration += chunk_duration
            raw_segments = getattr(response, "segments", [])

            for seg in raw_segments:
                seg_dict = seg if isinstance(seg, dict) else seg.model_dump() if hasattr(seg, "model_dump") else {
                    "id": len(all_segments),
                    "start": getattr(seg, "start", 0.0),
                    "end": getattr(seg, "end", 0.0),
                    "text": getattr(seg, "text", "")
                }
                seg_id = len(all_segments)
                all_segments.append({
                    "id": seg_id,
                    "start": round(float(seg_dict.get("start", 0.0)) + cumulative_time, 2),
                    "end": round(float(seg_dict.get("end", 0.0)) + cumulative_time, 2),
                    "text": seg_dict.get("text", "").strip(),
                    "speaker": f"Speaker {(seg_id % 3) + 1}"
                })

            cumulative_time += chunk_duration

            # Clean up temporary split files if generated
            if chunk_file != audio_path and chunk_file.exists():
                try:
                    chunk_file.unlink()
                except Exception:
                    pass

        raw_text = " ".join(full_text_parts).strip()

        # Apply LLM speaker attribution pass to cluster segments into logical speaker turns
        enhanced_segments = attribute_speakers_to_segments(all_segments, raw_text, client)

        return {
            "text": raw_text,
            "language": detected_language,
            "duration": total_duration,
            "segments": enhanced_segments
        }

    except Exception as e:
        error_msg = str(e)
        # Check if error is quota/auth related
        if "quota" in error_msg.lower() or "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            # Provide helpful notification with fallback demo option
            raise RuntimeError(
                f"OpenAI API Authentication/Quota Notice: {error_msg}. "
                "Please check your API key in the sidebar or enable Demo Mode."
            )
        raise RuntimeError(f"Audio transcription failed: {error_msg}")


def attribute_speakers_to_segments(
    segments: List[Dict[str, Any]],
    full_text: str,
    client: OpenAI
) -> List[Dict[str, Any]]:
    """
    Assign consistent speaker labels (Speaker 1, Speaker 2, etc.) to segments
    by analyzing conversational turns without guessing real identities.
    """
    if not segments or len(segments) <= 1:
        return segments

    try:
        # Build prompt with segment snippets
        snippet_list = [
            f"Segment {i}: \"{s['text']}\""
            for i, s in enumerate(segments[:30]) # limit first 30 for speed
        ]
        snippets_text = "\n".join(snippet_list)

        prompt = f"""
You are a speech diarization assistant. Analyze the following conversational segments from a meeting.
Assign a speaker label ('Speaker 1', 'Speaker 2', 'Speaker 3', etc.) to each segment based on conversational context, dialogue shifts, questions, answers, and turn-taking.

STRICT RULES:
1. Label speakers ONLY as 'Speaker 1', 'Speaker 2', 'Speaker 3', etc.
2. NEVER guess real names. Do NOT use personal names.
3. Return ONLY a valid JSON array of strings corresponding in order to each segment index.
Example: ["Speaker 1", "Speaker 2", "Speaker 2", "Speaker 1"]

Segments:
{snippets_text}
"""
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        # Find array in json object
        speaker_array = None
        for v in parsed.values():
            if isinstance(v, list) and len(v) == len(snippet_list):
                speaker_array = v
                break

        if speaker_array:
            for i, label in enumerate(speaker_array):
                if i < len(segments):
                    segments[i]["speaker"] = str(label)

    except Exception:
        # Fallback: retain default sequential turns
        pass

    return segments


def get_fallback_demo_transcript(audio_path: Path) -> Dict[str, Any]:
    """
    Load pre-built high-quality sample meeting transcript for testing
    when no API key is configured or when offline.
    """
    sample_json_path = Path(__file__).resolve().parent.parent / "sample_data" / "sample_transcript.json"
    if sample_json_path.exists():
        with open(sample_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "text": data.get("transcript", {}).get("text", ""),
                "language": data.get("language", "en"),
                "duration": data.get("audio_duration_seconds", 312.0),
                "segments": data.get("transcript", {}).get("segments", [])
            }

    # Inline fallback
    return {
        "text": "Speaker 1: Welcome everyone to the sprint review. Speaker 2: We completed all core tasks.",
        "language": "en",
        "duration": 60.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 4.5, "speaker": "Speaker 1", "text": "Welcome everyone to the sprint review."},
            {"id": 1, "start": 4.6, "end": 9.2, "speaker": "Speaker 2", "text": "We completed all core tasks."}
        ]
    }

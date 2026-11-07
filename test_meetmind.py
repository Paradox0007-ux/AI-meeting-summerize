"""
Comprehensive Test Script for MeetMind
Tests database operations, audio processing, PDF generation, CSV export, and summarization schemas.
"""

import sys
import json
from pathlib import Path

def run_tests():
    print("=== Running MeetMind Comprehensive Tests ===")

    # 1. Test Database
    print("\n[1/5] Testing Database Manager...")
    from database import init_db, save_meeting, get_all_meetings, get_meeting_details, update_action_item_status
    init_db()

    # Load sample meeting
    sample_json = Path(__file__).resolve().parent / "sample_data" / "sample_transcript.json"
    with open(sample_json, "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    meeting_id = save_meeting(sample_data)
    print(f"  -> Successfully saved meeting with ID: {meeting_id}")

    meetings = get_all_meetings()
    assert len(meetings) > 0, "No meetings retrieved from database"
    print(f"  -> Successfully retrieved {len(meetings)} meetings from database")

    details = get_meeting_details(meeting_id)
    assert details is not None, "Failed to fetch meeting details"
    assert len(details["action_items"]) > 0, "No action items found in details"
    assert len(details["decisions"]) > 0, "No decisions found in details"
    print(f"  -> Verified meeting details: {len(details['action_items'])} action items, {len(details['decisions'])} decisions")

    # Test status update
    first_item_id = details["action_items"][0]["id"]
    update_res = update_action_item_status(first_item_id, "Completed")
    assert update_res, "Failed to update action item status"
    print(f"  -> Successfully updated action item #{first_item_id} status to Completed")

    # Test adding and deleting action item
    from database import add_action_item, delete_action_item
    new_task_id = add_action_item(
        meeting_id=meeting_id,
        task_description="Setup CI/CD deployment pipeline",
        assigned_person="Alex Turner",
        deadline="Next Monday",
        priority="High",
        status="Pending"
    )
    assert new_task_id > 0, "Failed to add manual action item"
    print(f"  -> Successfully added new action item #{new_task_id}")
    del_res = delete_action_item(new_task_id)
    assert del_res, "Failed to delete action item"
    print(f"  -> Successfully deleted test action item #{new_task_id}")

    # 2. Test Audio Service
    print("\n[2/5] Testing Audio Service...")
    from services.audio_service import get_sample_meeting_audio, get_audio_duration_seconds
    sample_wav = get_sample_meeting_audio()
    assert sample_wav.exists(), "Sample audio file was not generated"
    dur = get_audio_duration_seconds(sample_wav)
    print(f"  -> Sample audio verified at {sample_wav.name} (Duration: {dur}s)")

    # 3. Test Export Service (PDF, CSV, TXT, Markdown)
    print("\n[3/5] Testing Export Service...")
    from services.export_service import (
        generate_pdf_report,
        generate_action_items_csv,
        generate_transcript_txt,
        generate_markdown_summary
    )
    pdf_bytes = generate_pdf_report(details)
    assert len(pdf_bytes) > 1000, f"Generated PDF is too small ({len(pdf_bytes)} bytes)"
    print(f"  -> Generated PDF Report successfully ({len(pdf_bytes)} bytes)")

    csv_str = generate_action_items_csv(details["action_items"])
    assert "Task Description" in csv_str and "Assignee" in csv_str
    print(f"  -> Generated Action Items CSV successfully ({len(csv_str)} characters)")

    txt_str = generate_transcript_txt(details)
    assert "MEETMIND TRANSCRIPT REPORT" in txt_str
    print(f"  -> Generated TXT transcript successfully ({len(txt_str)} characters)")

    md_str = generate_markdown_summary(details)
    assert "# MeetMind" in md_str
    print(f"  -> Generated Markdown summary successfully ({len(md_str)} characters)")

    # 4. Test Pydantic Anti-Hallucination Schema Validation
    print("\n[4/5] Testing Pydantic Anti-Hallucination Schema...")
    from services.summarization_service import ActionItemSchema, MeetingReportSchema

    # Test that missing assignee or deadline defaults strictly to 'Not specified'
    test_action = ActionItemSchema(task_description="Build API endpoint")
    assert test_action.assigned_person == "Not specified", f"Expected 'Not specified', got {test_action.assigned_person}"
    assert test_action.deadline == "Not specified", f"Expected 'Not specified', got {test_action.deadline}"
    print("  -> Verified missing assignee & deadline correctly set to 'Not specified'")

    test_action_blank = ActionItemSchema(
        task_description="Refactor DB",
        assigned_person="None",
        deadline="N/A"
    )
    assert test_action_blank.assigned_person == "Not specified"
    assert test_action_blank.deadline == "Not specified"
    print("  -> Verified 'None'/'N/A' properly sanitized to 'Not specified'")

    # 5. Test Fallback Summarization & Transcription
    print("\n[5/5] Testing Offline/Demo Fallback Engines...")
    from services.transcription_service import transcribe_audio_file
    from services.summarization_service import generate_meeting_summary

    # Call with dummy key / offline
    demo_transcription = transcribe_audio_file(sample_wav, api_key="")
    assert len(demo_transcription["text"]) > 0, "Demo transcription failed"
    print(f"  -> Demo transcription verified ({len(demo_transcription['segments'])} segments)")

    demo_summary = generate_meeting_summary(demo_transcription["text"], api_key="")
    assert demo_summary.title, "Demo summarization failed"
    print(f"  -> Demo summarization verified: '{demo_summary.title}'")

    # Test Meeting Copilot Q&A
    from services.summarization_service import ask_meeting_copilot
    copilot_ans = ask_meeting_copilot(details, "What was decided?", api_key="")
    assert len(copilot_ans) > 10, "Copilot answer was empty"
    print(f"  -> Demo AI Copilot Q&A verified ({len(copilot_ans)} characters)")

    print("\n==========================================")
    print("SUCCESS: ALL MEETMIND TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()

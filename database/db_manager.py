"""
Database Manager for MeetMind
Uses SQLite to store meetings, transcripts, summaries, action items, and decisions.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection with Row factory enabled."""
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables with complete schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        audio_filename TEXT,
        audio_filesize_bytes INTEGER DEFAULT 0,
        audio_duration_seconds REAL DEFAULT 0.0,
        language TEXT DEFAULT 'en',
        overview TEXT,
        executive_summary TEXT,
        detailed_summary TEXT,
        unresolved_questions TEXT, -- JSON array of strings
        next_steps TEXT,           -- JSON array of strings
        status TEXT DEFAULT 'processed'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        full_text TEXT NOT NULL,
        segments_json TEXT, -- JSON array of segments [{speaker, start, end, text}]
        FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS action_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        task_description TEXT NOT NULL,
        assigned_person TEXT DEFAULT 'Not specified',
        deadline TEXT DEFAULT 'Not specified',
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        decision_text TEXT NOT NULL,
        context_topic TEXT,
        problem_discussed TEXT,
        proposed_solution TEXT,
        FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS key_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        topic TEXT,
        point_text TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()


def save_meeting(meeting_data: Dict[str, Any]) -> int:
    """
    Save complete meeting record, including transcript, action items, decisions, and key points.
    Returns the created meeting ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO meetings (
                title, audio_filename, audio_filesize_bytes, audio_duration_seconds,
                language, overview, executive_summary, detailed_summary,
                unresolved_questions, next_steps, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting_data.get("title", "Untitled Meeting"),
            meeting_data.get("audio_filename", ""),
            meeting_data.get("audio_filesize_bytes", 0),
            meeting_data.get("audio_duration_seconds", 0.0),
            meeting_data.get("language", "en"),
            meeting_data.get("overview", ""),
            meeting_data.get("executive_summary", ""),
            meeting_data.get("detailed_summary", ""),
            json.dumps(meeting_data.get("unresolved_questions", [])),
            json.dumps(meeting_data.get("next_steps", [])),
            meeting_data.get("status", "processed")
        ))
        meeting_id = cursor.lastrowid

        # Save transcript
        transcript_data = meeting_data.get("transcript", {})
        if isinstance(transcript_data, str):
            full_text = transcript_data
            segments_json = json.dumps([])
        else:
            full_text = transcript_data.get("text", "")
            segments_json = json.dumps(transcript_data.get("segments", []))

        cursor.execute("""
            INSERT INTO transcripts (meeting_id, full_text, segments_json)
            VALUES (?, ?, ?)
        """, (meeting_id, full_text, segments_json))

        # Save action items
        action_items = meeting_data.get("action_items", [])
        for item in action_items:
            cursor.execute("""
                INSERT INTO action_items (meeting_id, task_description, assigned_person, deadline, priority, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                item.get("task_description", ""),
                item.get("assigned_person", "Not specified") or "Not specified",
                item.get("deadline", "Not specified") or "Not specified",
                item.get("priority", "Medium") or "Medium",
                item.get("status", "Pending") or "Pending"
            ))

        # Save decisions
        decisions = meeting_data.get("decisions", [])
        for dec in decisions:
            cursor.execute("""
                INSERT INTO decisions (meeting_id, decision_text, context_topic, problem_discussed, proposed_solution)
                VALUES (?, ?, ?, ?, ?)
            """, (
                meeting_id,
                dec.get("decision_text", ""),
                dec.get("context_topic", ""),
                dec.get("problem_discussed", ""),
                dec.get("proposed_solution", "")
            ))

        # Save key discussion points
        key_points = meeting_data.get("key_discussion_points", [])
        for kp in key_points:
            topic = kp.get("topic", "") if isinstance(kp, dict) else ""
            point_text = kp.get("point_text", "") if isinstance(kp, dict) else str(kp)
            cursor.execute("""
                INSERT INTO key_points (meeting_id, topic, point_text)
                VALUES (?, ?, ?)
            """, (meeting_id, topic, point_text))

        conn.commit()
        return meeting_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_all_meetings() -> List[Dict[str, Any]]:
    """Retrieve all meetings with count of action items and decisions for dashboard list."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.*,
            (SELECT COUNT(*) FROM action_items a WHERE a.meeting_id = m.id) AS action_items_count,
            (SELECT COUNT(*) FROM decisions d WHERE d.meeting_id = m.id) AS decisions_count
        FROM meetings m
        ORDER BY m.created_at DESC
    """)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_meeting_details(meeting_id: int) -> Optional[Dict[str, Any]]:
    """Fetch complete details of a single meeting by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    meeting_row = cursor.fetchone()
    if not meeting_row:
        conn.close()
        return None

    meeting = dict(meeting_row)
    # Parse JSON fields
    try:
        meeting["unresolved_questions"] = json.loads(meeting.get("unresolved_questions") or "[]")
    except Exception:
        meeting["unresolved_questions"] = []

    try:
        meeting["next_steps"] = json.loads(meeting.get("next_steps") or "[]")
    except Exception:
        meeting["next_steps"] = []

    # Get transcript
    cursor.execute("SELECT * FROM transcripts WHERE meeting_id = ?", (meeting_id,))
    t_row = cursor.fetchone()
    if t_row:
        t_dict = dict(t_row)
        try:
            segments = json.loads(t_dict.get("segments_json") or "[]")
        except Exception:
            segments = []
        meeting["transcript"] = {
            "text": t_dict.get("full_text", ""),
            "segments": segments
        }
    else:
        meeting["transcript"] = {"text": "", "segments": []}

    # Get action items
    cursor.execute("SELECT * FROM action_items WHERE meeting_id = ? ORDER BY id ASC", (meeting_id,))
    meeting["action_items"] = [dict(r) for r in cursor.fetchall()]

    # Get decisions
    cursor.execute("SELECT * FROM decisions WHERE meeting_id = ? ORDER BY id ASC", (meeting_id,))
    meeting["decisions"] = [dict(r) for r in cursor.fetchall()]

    # Get key points
    cursor.execute("SELECT * FROM key_points WHERE meeting_id = ? ORDER BY id ASC", (meeting_id,))
    meeting["key_discussion_points"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return meeting


def update_action_item_status(item_id: int, new_status: str) -> bool:
    """Update status of a specific action item (Pending, In Progress, Completed)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE action_items SET status = ? WHERE id = ?", (new_status, item_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def add_action_item(
    meeting_id: int,
    task_description: str,
    assigned_person: str = "Not specified",
    deadline: str = "Not specified",
    priority: str = "Medium",
    status: str = "Pending"
) -> int:
    """Add a new action item to an existing meeting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO action_items (meeting_id, task_description, assigned_person, deadline, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        meeting_id,
        task_description.strip(),
        assigned_person.strip() or "Not specified",
        deadline.strip() or "Not specified",
        priority,
        status
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def delete_action_item(item_id: int) -> bool:
    """Delete an individual action item by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM action_items WHERE id = ?", (item_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def delete_meeting(meeting_id: int) -> bool:
    """Delete a meeting and all associated child records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM action_items WHERE meeting_id = ?", (meeting_id,))
    cursor.execute("DELETE FROM decisions WHERE meeting_id = ?", (meeting_id,))
    cursor.execute("DELETE FROM key_points WHERE meeting_id = ?", (meeting_id,))
    cursor.execute("DELETE FROM transcripts WHERE meeting_id = ?", (meeting_id,))
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_dashboard_metrics() -> Dict[str, Any]:
    """Calculate aggregate metrics for the dashboard overview."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM meetings")
    total_meetings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM action_items")
    total_action_items = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM action_items WHERE status = 'Completed'")
    completed_actions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM decisions")
    total_decisions = cursor.fetchone()[0]

    cursor.execute("SELECT priority, COUNT(*) as count FROM action_items GROUP BY priority")
    priority_counts = {row["priority"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT status, COUNT(*) as count FROM action_items GROUP BY status")
    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT COALESCE(SUM(audio_duration_seconds), 0) FROM meetings")
    total_duration_sec = cursor.fetchone()[0]

    conn.close()
    return {
        "total_meetings": total_meetings,
        "total_action_items": total_action_items,
        "completed_actions": completed_actions,
        "pending_actions": total_action_items - completed_actions,
        "total_decisions": total_decisions,
        "priority_distribution": priority_counts,
        "status_distribution": status_counts,
        "total_duration_minutes": round(total_duration_sec / 60, 1)
    }

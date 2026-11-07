"""
Export Service for MeetMind
Generates professional PDF executive reports (ReportLab), action items CSV (Pandas),
plain text transcripts, and formatted clipboard markdown.
"""

import io
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' in footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        # Header
        self.drawString(54, letter[1] - 36, "MeetMind — Executive Meeting Intelligence Report")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Footer
        self.line(54, 45, letter[0] - 54, 45)
        self.drawString(54, 32, "Confidential — For Internal Team Use Only")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_text)
        self.restoreState()


def generate_pdf_report(meeting: Dict[str, Any]) -> bytes:
    """
    Generate an executive-ready PDF report of the meeting.
    Returns PDF bytes buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    brand_blue = colors.HexColor("#2563EB")
    dark_slate = colors.HexColor("#0F172A")
    body_color = colors.HexColor("#334155")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=dark_slate,
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        "H1Style",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=brand_blue,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=body_color,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748B")
    )

    story = []

    # Title & Metadata
    title = meeting.get("title", "Meeting Report")
    story.append(Paragraph(title, title_style))

    created_at = meeting.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
    duration = meeting.get("audio_duration_seconds", 0)
    duration_str = f"{int(duration // 60)}m {int(duration % 60)}s" if duration else "N/A"
    lang = meeting.get("language", "en").upper()
    filename = meeting.get("audio_filename", "Audio Recording")

    meta_text = f"<b>Date:</b> {created_at} &nbsp;|&nbsp; <b>Duration:</b> {duration_str} &nbsp;|&nbsp; <b>Language:</b> {lang} &nbsp;|&nbsp; <b>File:</b> {filename}"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=4, spaceAfter=12))

    # Executive Overview
    overview = meeting.get("overview") or meeting.get("executive_summary") or "No summary available."
    story.append(Paragraph("Executive Summary", h1_style))
    
    # Overview in a styled callout box
    overview_p = Paragraph(f"<i>{overview}</i>", body_style)
    overview_table = Table([[overview_p]], colWidths=[letter[0] - 108])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 10))

    # Detailed Summary
    detailed = meeting.get("detailed_summary")
    if detailed:
        story.append(Paragraph("Detailed Discussion Summary", h1_style))
        story.append(Paragraph(detailed, body_style))
        story.append(Spacer(1, 8))

    # Key Discussion Points
    points = meeting.get("key_discussion_points", [])
    if points:
        story.append(Paragraph("Key Discussion Points", h1_style))
        for kp in points:
            topic = kp.get("topic", "") if isinstance(kp, dict) else ""
            p_text = kp.get("point_text", "") if isinstance(kp, dict) else str(kp)
            bullet_html = f"&bull; <b>{topic}:</b> {p_text}" if topic else f"&bull; {p_text}"
            story.append(Paragraph(bullet_html, body_style))
        story.append(Spacer(1, 8))

    # Decisions Made
    decisions = meeting.get("decisions", [])
    if decisions:
        story.append(Paragraph("Important Decisions & Agreements", h1_style))
        dec_data = [
            [
                Paragraph("<b>Decision / Agreement</b>", body_bold),
                Paragraph("<b>Context & Problem</b>", body_bold),
                Paragraph("<b>Proposed Solution</b>", body_bold)
            ]
        ]
        for d in decisions:
            dec_text = Paragraph(d.get("decision_text", ""), body_style)
            problem = Paragraph(f"<b>{d.get('context_topic', '')}</b><br/>{d.get('problem_discussed', '')}", body_style)
            solution = Paragraph(d.get("proposed_solution", ""), body_style)
            dec_data.append([dec_text, problem, solution])

        dec_col_widths = [190, 160, 154]
        dec_table = Table(dec_data, colWidths=dec_col_widths)
        dec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(dec_table)
        story.append(Spacer(1, 10))

    # Action Items Table
    action_items = meeting.get("action_items", [])
    if action_items:
        story.append(Paragraph("Action Items & Deliverables", h1_style))
        act_data = [
            [
                Paragraph("<b>Task Description</b>", body_bold),
                Paragraph("<b>Assignee</b>", body_bold),
                Paragraph("<b>Deadline</b>", body_bold),
                Paragraph("<b>Priority</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
            ]
        ]
        for a in action_items:
            task_p = Paragraph(a.get("task_description", ""), body_style)
            assignee_p = Paragraph(a.get("assigned_person", "Not specified"), body_style)
            deadline_p = Paragraph(a.get("deadline", "Not specified"), body_style)
            priority = a.get("priority", "Medium")
            status = a.get("status", "Pending")

            act_data.append([
                task_p,
                assignee_p,
                deadline_p,
                Paragraph(priority, body_style),
                Paragraph(status, body_style)
            ])

        act_col_widths = [204, 85, 85, 65, 65]
        act_table = Table(act_data, colWidths=act_col_widths)
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(act_table)
        story.append(Spacer(1, 10))

    # Next Steps & Questions
    next_steps = meeting.get("next_steps", [])
    questions = meeting.get("unresolved_questions", [])
    if next_steps or questions:
        story.append(Paragraph("Next Steps & Open Questions", h1_style))
        if next_steps:
            for s in next_steps:
                story.append(Paragraph(f"&rarr; <b>Next Step:</b> {s}", body_style))
        if questions:
            for q in questions:
                story.append(Paragraph(f"? <b>Open Question:</b> {q}", body_style))
        story.append(Spacer(1, 10))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


def generate_action_items_csv(action_items: List[Dict[str, Any]]) -> str:
    """Generate CSV string of action items using Pandas."""
    if not action_items:
        df = pd.DataFrame(columns=["Task Description", "Assignee", "Deadline", "Priority", "Status"])
    else:
        cleaned = []
        for item in action_items:
            cleaned.append({
                "Task Description": item.get("task_description", ""),
                "Assignee": item.get("assigned_person", "Not specified") or "Not specified",
                "Deadline": item.get("deadline", "Not specified") or "Not specified",
                "Priority": item.get("priority", "Medium"),
                "Status": item.get("status", "Pending")
            })
        df = pd.DataFrame(cleaned)

    return df.to_csv(index=False)


def generate_transcript_txt(meeting: Dict[str, Any]) -> str:
    """Generate clean TXT transcript with timestamps and speaker labels."""
    transcript = meeting.get("transcript", {})
    title = meeting.get("title", "Meeting")
    created_at = meeting.get("created_at", "")

    lines = [
        f"MEETMIND TRANSCRIPT REPORT",
        f"Meeting: {title}",
        f"Date: {created_at}",
        "=" * 60,
        ""
    ]

    segments = transcript.get("segments", [])
    if segments:
        for seg in segments:
            speaker = seg.get("speaker", "Speaker")
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            text = seg.get("text", "")
            time_tag = f"[{int(start // 60):02d}:{int(start % 60):02d} - {int(end // 60):02d}:{int(end % 60):02d}]"
            lines.append(f"{time_tag} {speaker}: {text}")
            lines.append("")
    else:
        full_text = transcript.get("text", "") if isinstance(transcript, dict) else str(transcript)
        lines.append(full_text)

    return "\n".join(lines)


def generate_markdown_summary(meeting: Dict[str, Any]) -> str:
    """Generate a clean markdown report representation for clipboard copying."""
    title = meeting.get("title", "Meeting Report")
    overview = meeting.get("overview", "")
    exec_summary = meeting.get("executive_summary", "")
    detailed = meeting.get("detailed_summary", "")

    md = [
        f"# {title}",
        f"**Date:** {meeting.get('created_at', 'N/A')} | **Duration:** {meeting.get('audio_duration_seconds', 0)}s",
        "",
        "## Overview",
        overview,
        "",
        "## Executive Summary",
        exec_summary,
        "",
        "## Detailed Summary",
        detailed,
        "",
        "## Important Decisions",
    ]

    for d in meeting.get("decisions", []):
        md.append(f"- **{d.get('decision_text')}** (Topic: {d.get('context_topic', 'General')})")
        if d.get("problem_discussed"):
            md.append(f"  - *Problem:* {d.get('problem_discussed')}")
        if d.get("proposed_solution"):
            md.append(f"  - *Solution:* {d.get('proposed_solution')}")

    md.extend(["", "## Action Items"])
    for a in meeting.get("action_items", []):
        md.append(
            f"- [{ 'x' if a.get('status') == 'Completed' else ' ' }] "
            f"**{a.get('task_description')}** | Assignee: {a.get('assigned_person', 'Not specified')} | "
            f"Due: {a.get('deadline', 'Not specified')} | Priority: {a.get('priority', 'Medium')} | Status: {a.get('status', 'Pending')}"
        )

    if meeting.get("unresolved_questions"):
        md.extend(["", "## Open Questions"])
        for q in meeting.get("unresolved_questions", []):
            md.append(f"- ? {q}")

    if meeting.get("next_steps"):
        md.extend(["", "## Next Steps"])
        for s in meeting.get("next_steps", []):
            md.append(f"- &rarr; {s}")

    return "\n".join(md)

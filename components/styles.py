"""
CSS Styles and Visual Design System for MeetMind
Provides a modern SaaS theme with cards, status pills, speaker tags, and responsive design.
"""

def get_custom_css(is_dark_mode: bool = False) -> str:
    """Return inject-able CSS for modern SaaS styling."""
    
    # Theme color palettes
    if is_dark_mode:
        bg_card = "#1E293B"
        border_color = "#334155"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        accent_blue = "#3B82F6"
        card_hover_shadow = "0 8px 24px -4px rgba(0, 0, 0, 0.4)"
        sidebar_bg = "#0F172A"
    else:
        bg_card = "#FFFFFF"
        border_color = "#E2E8F0"
        text_primary = "#0F172A"
        text_secondary = "#64748B"
        accent_blue = "#2563EB"
        card_hover_shadow = "0 10px 25px -5px rgba(37, 99, 235, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)"
        sidebar_bg = "#F8FAFC"

    return f"""
    <style>
        /* Global resets and typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        /* Header styling */
        .main-header {{
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 1px solid {border_color};
        }}
        .brand-title {{
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;
            display: inline-block;
            margin-bottom: 4px;
        }}
        .brand-subtitle {{
            font-size: 0.95rem;
            color: {text_secondary};
            font-weight: 400;
        }}

        /* Modern SaaS Card */
        .saas-card {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease-in-out;
        }}
        .saas-card:hover {{
            box-shadow: {card_hover_shadow};
            border-color: {accent_blue};
        }}

        /* Metric cards */
        .metric-card {{
            background: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px 20px;
            text-align: left;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            border-left: 4px solid {accent_blue};
        }}
        .metric-card.success {{ border-left-color: #10B981; }}
        .metric-card.warning {{ border-left-color: #F59E0B; }}
        .metric-card.purple {{ border-left-color: #8B5CF6; }}

        .metric-val {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {text_primary};
            line-height: 1.2;
        }}
        .metric-lbl {{
            font-size: 0.82rem;
            font-weight: 500;
            color: {text_secondary};
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 4px;
        }}

        /* Status & Priority Badges */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 9999px;
            text-align: center;
        }}
        .badge-high {{ background-color: #FEE2E2; color: #DC2626; border: 1px solid #FECACA; }}
        .badge-med {{ background-color: #FEF3C7; color: #D97706; border: 1px solid #FDE68A; }}
        .badge-low {{ background-color: #E0E7FF; color: #4F46E5; border: 1px solid #C7D2FE; }}

        .badge-pending {{ background-color: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }}
        .badge-progress {{ background-color: #DBEAFE; color: #1D4ED8; border: 1px solid #BFDBFE; }}
        .badge-done {{ background-color: #D1FAE5; color: #047857; border: 1px solid #A7F3D0; }}

        /* Speaker Pills */
        .speaker-badge {{
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 8px;
            font-family: 'JetBrains Mono', monospace;
        }}
        .speaker-1 {{ background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }}
        .speaker-2 {{ background: #F5F3FF; color: #6D28D9; border: 1px solid #DDD6FE; }}
        .speaker-3 {{ background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }}
        .speaker-4 {{ background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }}

        /* Transcript Dialogue Block */
        .transcript-line {{
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid transparent;
            background: {bg_card};
            border: 1px solid {border_color};
        }}
        .transcript-time {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: {text_secondary};
            margin-right: 8px;
        }}
        .transcript-text {{
            font-size: 0.92rem;
            color: {text_primary};
            line-height: 1.5;
            margin-top: 4px;
        }}

        /* Decision card callout */
        .decision-card {{
            border-left: 4px solid #10B981;
            background: {bg_card};
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            border-top: 1px solid {border_color};
            border-right: 1px solid {border_color};
            border-bottom: 1px solid {border_color};
        }}
        .decision-title {{
            font-weight: 700;
            font-size: 0.95rem;
            color: {text_primary};
            margin-bottom: 4px;
        }}
        .decision-meta {{
            font-size: 0.82rem;
            color: {text_secondary};
            margin-top: 4px;
        }}

        /* Sleek Button Enhancements */
        div.stButton > button:first-child {{
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.88rem;
            transition: all 0.15s ease-in-out;
        }}

        /* Code & Monospace */
        code {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.85em !important;
        }}
    </style>
    """

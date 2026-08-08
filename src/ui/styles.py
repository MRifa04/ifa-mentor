# IFA Mentor — Dark Theme Styles

COLORS = {
    "bg_primary":    "#0A0F1E",
    "bg_secondary":  "#0F172A",
    "bg_card":       "#131C31",
    "bg_hover":      "#1E293B",
    "accent_blue":   "#3B82F6",
    "accent_green":  "#10B981",
    "accent_purple": "#8B5CF6",
    "accent_orange": "#F59E0B",
    "accent_red":    "#EF4444",
    "text_primary":  "#F1F5F9",
    "text_secondary":"#94A3B8",
    "text_muted":    "#475569",
    "border":        "#1E293B",
    "sidebar_width": "220px",
}

MAIN_STYLE = """
QMainWindow, QWidget {
    background-color: #0A0F1E;
    color: #F1F5F9;
    font-family: 'Segoe UI', Arial, sans-serif;
}

/* ── SIDEBAR ── */
#sidebar {
    background-color: #0F172A;
    border-right: 1px solid #1E293B;
    min-width: 220px;
    max-width: 220px;
}

#logo_label {
    color: #F1F5F9;
    font-size: 20px;
    font-weight: bold;
    padding: 20px;
}

#logo_sub {
    color: #3B82F6;
    font-size: 11px;
    padding: 0px 20px 20px 20px;
}

/* ── NAV BUTTONS ── */
#nav_btn {
    background: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    margin: 2px 8px;
}

#nav_btn:hover {
    background-color: #1E293B;
    color: #F1F5F9;
}

#nav_btn_active {
    background-color: #1E3A5F;
    color: #3B82F6;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: bold;
    margin: 2px 8px;
    border-left: 3px solid #3B82F6;
}

/* ── CARDS ── */
#card {
    background-color: #131C31;
    border-radius: 12px;
    border: 1px solid #1E293B;
    padding: 16px;
}

#card_title {
    color: #3B82F6;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}

/* ── PROGRESS BAR ── */
QProgressBar {
    background-color: #1E293B;
    border-radius: 4px;
    height: 6px;
    border: none;
}

QProgressBar::chunk {
    border-radius: 4px;
    background-color: #3B82F6;
}

/* ── BUTTONS ── */
#btn_primary {
    background-color: #3B82F6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
}

#btn_primary:hover {
    background-color: #2563EB;
}

#btn_primary:pressed {
    background-color: #1D4ED8;
}

#btn_secondary {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
}

#btn_secondary:hover {
    background-color: #334155;
    color: #F1F5F9;
}

/* ── SKILL BUTTONS ── */
#btn_listening {
    background-color: #1E1B4B;
    color: #818CF8;
    border: 1px solid #3730A3;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
}

#btn_reading {
    background-color: #052E16;
    color: #34D399;
    border: 1px solid #065F46;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
}

#btn_speaking {
    background-color: #1E3A5F;
    color: #60A5FA;
    border: 1px solid #1D4ED8;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
}

#btn_writing {
    background-color: #2D1B4E;
    color: #C084FC;
    border: 1px solid #6D28D9;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
}

#btn_vocab {
    background-color: #1C3D2A;
    color: #4ADE80;
    border: 1px solid #166534;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
}

/* ── INPUT ── */
QLineEdit, QTextEdit {
    background-color: #131C31;
    color: #F1F5F9;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3B82F6;
}

/* ── SCROLL BAR ── */
QScrollBar:vertical {
    background: #0F172A;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 3px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── SPLITTER ── */
QSplitter::handle {
    background-color: #1E293B;
    width: 1px;
}

/* ── LABEL ── */
#title_large {
    font-size: 22px;
    font-weight: bold;
    color: #F1F5F9;
}

#title_medium {
    font-size: 16px;
    font-weight: bold;
    color: #F1F5F9;
}

#text_secondary {
    font-size: 12px;
    color: #94A3B8;
}

#text_accent {
    font-size: 12px;
    color: #3B82F6;
}

#score_large {
    font-size: 28px;
    font-weight: bold;
    color: #F1F5F9;
}

#badge_b1 {
    background-color: #1E3A5F;
    color: #60A5FA;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}

#badge_b2 {
    background-color: #052E16;
    color: #34D399;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}
"""

SKILL_COLORS = {
    "Reading":    "#10B981",
    "Listening":  "#8B5CF6",
    "Speaking":   "#3B82F6",
    "Writing":    "#C084FC",
    "Vocabulary": "#4ADE80",
    "Grammar":    "#F59E0B"
}

SKILL_ICONS = {
    "Home":       "🏠",
    "Study DNA":  "🧬",
    "Reading":    "📖",
    "Listening":  "🎧",
    "Speaking":   "🎤",
    "Writing":    "✍️",
    "Vocabulary": "📚",
    "Library":    "🗂️",
    "Mock Exams": "🎓",
    "Progress":   "📊",
    "Statistics": "📈",
    "Settings":   "⚙️"
}
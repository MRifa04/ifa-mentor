import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
    QSizePolicy,
    QScrollArea,
    QLineEdit,
    QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from config.settings import TARGET_LEVEL, CEFR_LEVELS
from src.user_profile import get_profile
from src.scores import (
    get_current_scores,
    get_weakest_skill,
    minutes_by_skill,
    EXAM_SKILL_NAMES,
    EXAM_SKILL_LABELS,
)

from src.ui.Voice.voice_assistant import VoiceAssistant


# ============================================================
# SIGNALS
# ============================================================

class DashboardSignals(QObject):

    plan_loaded = pyqtSignal(dict)
    goal_loaded = pyqtSignal(dict)
    ai_response = pyqtSignal(str)


# ============================================================
# SCORE CARD
# ============================================================

class ScoreCard(QFrame):

    def __init__(
        self,
        skill,
        score,
        color,
        today_min=0,
    ):
        super().__init__()

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }

            QFrame * {
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(6)

        # ----------------------------------------------------
        # SKILL
        # ----------------------------------------------------

        name_lbl = QLabel(skill)

        name_lbl.setStyleSheet(
            f"""
            QLabel {{
                color:{color};
                font-size:11px;
                font-weight:bold;
                background:transparent;
                border:none;
            }}
            """
        )

        layout.addWidget(name_lbl)

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        try:
            pct = int(
                min(
                    100,
                    (float(score) / 75) * 100,
                )
            )
        except Exception:
            pct = 0

        score_lbl = QLabel(
            f"{pct}%"
        )

        score_lbl.setStyleSheet("""
            QLabel {
                color:#F1F5F9;
                font-size:26px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
        """)

        layout.addWidget(score_lbl)

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        bar = QProgressBar()

        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setFixedHeight(4)

        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background:#1E293B;
                border-radius:2px;
                border:none;
            }}

            QProgressBar::chunk {{
                background:{color};
                border-radius:2px;
            }}
            """
        )

        layout.addWidget(bar)

        # ----------------------------------------------------
        # TODAY
        # ----------------------------------------------------

        today_lbl = QLabel(
            f"Bugungi dars  {today_min} min"
        )

        today_lbl.setStyleSheet("""
            QLabel {
                color:#475569;
                font-size:10px;
                background:transparent;
                border:none;
            }
        """)

        layout.addWidget(today_lbl)


# ============================================================
# MISSION CARD
# ============================================================

class MissionCard(QFrame):

    def __init__(
        self,
        tasks,
        on_start,
        level=TARGET_LEVEL,
    ):
        super().__init__()

        self.tasks = [
            task for task in tasks
            if task.get("skill") in EXAM_SKILL_LABELS
        ]
        self.level = level

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }

            QFrame * {
                background:transparent;
                border:none;
            }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            16,
            20,
            16,
        )

        layout.setSpacing(10)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "TODAY'S MISSION"
        )

        title.setStyleSheet("""
            QLabel {
                color:#3B82F6;
                font-size:11px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
        """)

        total_time = sum(
            int(
                task.get(
                    "duration_minutes",
                    task.get("duration", 0),
                ) or 0
            )
            for task in self.tasks
        )

        time_lbl = QLabel(
            f"⏱  {total_time} min"
        )

        time_lbl.setStyleSheet("""
            QLabel {
                color:#94A3B8;
                font-size:12px;
                background:transparent;
                border:none;
            }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(time_lbl)

        layout.addLayout(header)

        # ----------------------------------------------------
        # ICONS
        # ----------------------------------------------------

        skill_icons = {
            "Listening": ("🎧", "#8B5CF6"),
            "Reading": ("📖", "#10B981"),
            "Speaking": ("🎤", "#3B82F6"),
            "Writing": ("✍️", "#C084FC"),
        }

        # ----------------------------------------------------
        # TASKS
        # ----------------------------------------------------

        if not self.tasks:

            empty_lbl = QLabel(
                "Bugun uchun vazifalar mavjud emas."
            )

            empty_lbl.setStyleSheet("""
                QLabel {
                    color:#64748B;
                    font-size:12px;
                    background:transparent;
                    border:none;
                }
            """)

            empty_lbl.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            layout.addWidget(empty_lbl)

        else:

            for task in self.tasks:

                skill = task.get(
                    "skill",
                    "",
                )

                icon, color = skill_icons.get(
                    skill,
                    ("📄", "#94A3B8"),
                )

                duration = int(
                    task.get(
                        "duration_minutes",
                        task.get("duration", 0),
                    ) or 0
                )

                task_type = task.get(
                    "task_type",
                    "",
                )

                completed = task.get(
                    "is_completed",
                    0,
                )

                # ------------------------------------------------
                # ROW
                # ------------------------------------------------

                row = QFrame()

                row.setMinimumHeight(58)

                row.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Minimum,
                )

                row.setStyleSheet("""
                    QFrame {
                        background:#0F172A;
                        border-radius:8px;
                        border:1px solid #1E293B;
                    }

                    QFrame * {
                        background:transparent;
                        border:none;
                    }
                """)

                row_l = QHBoxLayout(row)

                row_l.setContentsMargins(
                    12,
                    7,
                    12,
                    7,
                )

                row_l.setSpacing(10)

                # ------------------------------------------------
                # ICON
                # ------------------------------------------------

                icon_lbl = QLabel(icon)

                icon_lbl.setFixedWidth(34)

                icon_lbl.setSizePolicy(
                    QSizePolicy.Policy.Fixed,
                    QSizePolicy.Policy.Preferred,
                )

                icon_lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                icon_lbl.setStyleSheet("""
                    QLabel {
                        color:#F1F5F9;
                        font-size:18px;
                        background:transparent;
                        border:none;
                    }
                """)

                # ------------------------------------------------
                # INFORMATION
                # ------------------------------------------------

                info_l = QVBoxLayout()

                info_l.setContentsMargins(
                    0,
                    0,
                    0,
                    0,
                )

                info_l.setSpacing(2)

                skill_lbl = QLabel(
                    f"{skill} — {self.level}"
                )

                skill_lbl.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred,
                )

                skill_lbl.setWordWrap(False)

                skill_lbl.setStyleSheet("""
                    QLabel {
                        color:#F1F5F9;
                        font-size:13px;
                        font-weight:bold;
                        background:transparent;
                        border:none;
                    }
                """)

                type_text = (
                    task_type
                    .replace("_", " ")
                    .title()
                )

                type_lbl = QLabel(
                    type_text
                )

                type_lbl.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred,
                )

                type_lbl.setWordWrap(False)

                type_lbl.setStyleSheet("""
                    QLabel {
                        color:#94A3B8;
                        font-size:11px;
                        background:transparent;
                        border:none;
                    }
                """)

                info_l.addWidget(skill_lbl)
                info_l.addWidget(type_lbl)

                # ------------------------------------------------
                # STATUS
                # ------------------------------------------------

                if completed:

                    status_text = "✅"
                    status_color = "#10B981"

                else:

                    status_text = (
                        f"{duration} min  ›"
                    )

                    status_color = "#94A3B8"

                status_lbl = QLabel(
                    status_text
                )

                status_lbl.setSizePolicy(
                    QSizePolicy.Policy.Fixed,
                    QSizePolicy.Policy.Preferred,
                )

                status_lbl.setAlignment(
                    Qt.AlignmentFlag.AlignRight |
                    Qt.AlignmentFlag.AlignVCenter
                )

                status_lbl.setStyleSheet(
                    f"""
                    QLabel {{
                        color:{status_color};
                        font-size:12px;
                        background:transparent;
                        border:none;
                    }}
                    """
                )

                # ------------------------------------------------
                # IMPORTANT LAYOUT
                # ------------------------------------------------

                row_l.addWidget(
                    icon_lbl
                )

                # Stretch factor = 1
                row_l.addLayout(
                    info_l,
                    1,
                )

                row_l.addWidget(
                    status_lbl
                )

                layout.addWidget(row)

        # ----------------------------------------------------
        # START BUTTON
        # ----------------------------------------------------

        start_btn = QPushButton(
            "▶  START SESSION"
        )

        start_btn.setFixedHeight(42)

        start_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        start_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        start_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;
                color:white;
                border:none;
                border-radius:8px;
                font-size:13px;
                font-weight:bold;
            }

            QPushButton:hover {
                background:#2563EB;
            }

            QPushButton:pressed {
                background:#1D4ED8;
            }
        """)

        start_btn.clicked.connect(
            on_start
        )

        layout.addWidget(
            start_btn
        )


# ============================================================
# GOAL PROGRESS CARD
# ============================================================

class GoalProgressCard(QFrame):

    def __init__(
        self,
        goal_data,
        db=None,
    ):
        super().__init__()

        self.goal_data = goal_data
        self.db = db

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E3A5F;
            }

            QFrame * {
                background:transparent;
                border:none;
            }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        layout.setSpacing(10)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "🎯 MAQSAD PROGRESSI"
        )

        title.setStyleSheet("""
            QLabel {
                color:#10B981;
                font-size:11px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
        """)

        target = goal_data.get(
            "target_level",
            "B2",
        )

        end_date = goal_data.get(
            "end_date",
            "",
        )

        date_lbl = QLabel(
            f"{target} → {end_date}"
        )

        date_lbl.setStyleSheet("""
            QLabel {
                color:#64748B;
                font-size:11px;
                background:transparent;
                border:none;
            }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(date_lbl)

        layout.addLayout(header)

        # ----------------------------------------------------
        # SCORES
        # ----------------------------------------------------

        current = get_current_scores(self.db).get(
            "overall",
            0,
        )

        target_score = goal_data.get(
            "target_overall",
            51,
        )

        try:
            current = float(current)
        except Exception:
            current = 0

        try:
            target_score = float(target_score)
        except Exception:
            target_score = 51

        prog_row = QHBoxLayout()

        prog_lbl = QLabel(
            f"{int(current)}/75"
        )

        prog_lbl.setStyleSheet("""
            QLabel {
                color:#F1F5F9;
                font-size:13px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
        """)

        target_lbl = QLabel(
            f"→ {int(target_score)}/75"
        )

        target_lbl.setStyleSheet("""
            QLabel {
                color:#10B981;
                font-size:13px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
        """)

        prog_row.addWidget(
            prog_lbl
        )

        prog_row.addStretch()

        prog_row.addWidget(
            target_lbl
        )

        layout.addLayout(
            prog_row
        )

        # ----------------------------------------------------
        # PROGRESS BAR
        # ----------------------------------------------------

        progress = 0

        if target_score > 0:

            progress = int(
                min(
                    100,
                    (current / target_score) * 100,
                )
            )

        prog_bar = QProgressBar()

        prog_bar.setValue(
            progress
        )

        prog_bar.setTextVisible(
            False
        )

        prog_bar.setFixedHeight(8)

        prog_bar.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:4px;
                border:none;
            }

            QProgressBar::chunk {
                background:#3B82F6;
                border-radius:4px;
            }
        """)

        layout.addWidget(
            prog_bar
        )

        # ----------------------------------------------------
        # DAILY GAIN
        # ----------------------------------------------------

        daily_gain = goal_data.get(
            "daily_gain_needed",
            0,
        )

        days = goal_data.get(
            "days",
            60,
        )

        gain_lbl = QLabel(
            f"Kuniga +{daily_gain} ball kerak  •  "
            f"{days} kun"
        )

        gain_lbl.setStyleSheet("""
            QLabel {
                color:#64748B;
                font-size:11px;
                background:transparent;
                border:none;
            }
        """)

        layout.addWidget(
            gain_lbl
        )


# ============================================================
# DASHBOARD
# ============================================================

class DashboardWidget(QWidget):

    def __init__(
        self,
        db,
        ai,
        on_start_task=None,
    ):
        super().__init__()

        self.db = db
        self.ai = ai
        self.on_start_task = on_start_task
        self.current_scores = get_current_scores(db)
        self.today_tasks = []
        self.profile = get_profile(db)
        self.display_level = self.profile.get(
            "target_level",
            TARGET_LEVEL,
        )

        # ----------------------------------------------------
        # VOICE ASSISTANT
        # ----------------------------------------------------

        try:
            self.voice_assistant = VoiceAssistant(
                db=self.db,
                ai=self.ai,
                user_name=self.profile["name"],
            )
        except Exception as e:
            print("VoiceAssistant xatosi:", e)
            self.voice_assistant = None

        # ----------------------------------------------------
        # SIGNALS
        # ----------------------------------------------------

        self.signals = DashboardSignals()
        self._load_generation = 0

        self.signals.plan_loaded.connect(
            self._update_mission
        )

        self.signals.goal_loaded.connect(
            self._update_goal
        )

        self.signals.ai_response.connect(
            self._show_ai_response
        )

        # ----------------------------------------------------
        # BUILD
        # ----------------------------------------------------

        self._build()

        # ----------------------------------------------------
        # LOAD
        # ----------------------------------------------------

        self._load_data()


# ============================================================
# BUILD
# ============================================================

    def _build(self):

        main = QHBoxLayout(self)

        main.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main.setSpacing(0)

        # ====================================================
        # LEFT CONTENT
        # ====================================================

        left_content = QWidget()

        left_content.setStyleSheet("""
            QWidget {
                background:#0A0F1E;
            }
        """)

        self.left_l = QVBoxLayout(
            left_content
        )

        self.left_l.setContentsMargins(
            28,
            24,
            20,
            24,
        )

        self.left_l.setSpacing(12)

        # ----------------------------------------------------
        # GREETING
        # ----------------------------------------------------

        hour = datetime.now().hour

        if hour < 12:
            greeting = "Good morning"

        elif hour >= 18:
            greeting = "Good evening"

        else:
            greeting = "Good afternoon"

        self.greet_lbl = QLabel(
            f"{greeting}, "
            f"{self.profile['name']}! 👋"
        )

        self.greet_lbl.setStyleSheet("""
            QLabel {
                font-size:24px;
                font-weight:bold;
                color:#F1F5F9;
                background:transparent;
                border:none;
            }
        """)

        self.left_l.addWidget(
            self.greet_lbl
        )

        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        self.sub_lbl = QLabel(
            self._profile_subtitle()
        )

        self.sub_lbl.setWordWrap(
            True
        )

        self.sub_lbl.setStyleSheet("""
            QLabel {
                color:#94A3B8;
                font-size:13px;
                background:transparent;
                border:none;
            }
        """)

        self.left_l.addWidget(
            self.sub_lbl
        )

        # ====================================================
        # SCORES
        # ====================================================

        scores_l = QHBoxLayout()

        scores_l.setSpacing(12)

        self.scores_row = scores_l
        self._populate_score_cards()

        self.left_l.addLayout(
            scores_l
        )

        # ====================================================
        # GOAL SLOT
        # ====================================================

        self.goal_slot = QFrame()

        self.goal_slot.setFixedHeight(
            0
        )

        self.goal_slot.setStyleSheet("""
            QFrame {
                background:transparent;
                border:none;
            }
        """)

        self.left_l.addWidget(
            self.goal_slot
        )

        # ====================================================
        # MISSION SLOT
        # ====================================================

        self.mission_slot = QFrame()

        self.mission_slot.setMinimumHeight(
            100
        )

        self.mission_slot.setStyleSheet("""
            QFrame {
                background:transparent;
                border:none;
            }
        """)

        mp_l = QVBoxLayout(
            self.mission_slot
        )

        mp_l.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        mp_l.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        loading = QLabel(
            "⏳ Kunlik reja yuklanmoqda..."
        )

        loading.setStyleSheet("""
            QLabel {
                color:#475569;
                font-size:13px;
                background:transparent;
                border:none;
            }
        """)

        loading.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        mp_l.addWidget(
            loading
        )

        self.left_l.addWidget(
            self.mission_slot
        )

        self.left_l.addStretch()

        # ====================================================
        # LEFT SCROLL
        # ====================================================

        self.left_scroll = QScrollArea()

        self.left_scroll.setWidgetResizable(
            True
        )

        self.left_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.left_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.left_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.left_scroll.setWidget(
            left_content
        )

        self.left_scroll.setStyleSheet("""
            QScrollArea {
                background:#0A0F1E;
                border:none;
            }

            QScrollBar:vertical {
                background:#0A0F1E;
                width:8px;
            }

            QScrollBar::handle:vertical {
                background:#334155;
                border-radius:4px;
                min-height:40px;
            }

            QScrollBar::handle:vertical:hover {
                background:#475569;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height:0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background:transparent;
            }
        """)

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right = QWidget()

        right.setFixedWidth(
            320
        )

        right.setStyleSheet("""
            QWidget {
                background:#0F172A;
                border-left:1px solid #1E293B;
            }
        """)

        right_l = QVBoxLayout(
            right
        )

        right_l.setContentsMargins(
            20,
            24,
            20,
            24,
        )

        right_l.setSpacing(14)

        # ====================================================
        # AI HEADER
        # ====================================================

        ai_header = QHBoxLayout()

        ai_icon = QLabel("⬡")

        ai_icon.setStyleSheet("""
            QLabel {
                font-size:18px;
                color:#3B82F6;
                background:transparent;
                border:none;
            }
        """)

        ai_title = QLabel(
            "IFA Mentor"
        )

        ai_title.setStyleSheet("""
            QLabel {
                font-size:14px;
                font-weight:bold;
                color:#F1F5F9;
                background:transparent;
                border:none;
            }
        """)

        ai_dot = QLabel(
            "● AI"
        )

        ai_dot.setStyleSheet("""
            QLabel {
                font-size:11px;
                color:#10B981;
                background:transparent;
                border:none;
            }
        """)

        ai_header.addWidget(
            ai_icon
        )

        ai_header.addWidget(
            ai_title
        )

        ai_header.addStretch()

        ai_header.addWidget(
            ai_dot
        )

        right_l.addLayout(
            ai_header
        )

        # ====================================================
        # AI MESSAGE
        # ====================================================

        ai_msg = QFrame()

        ai_msg.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }

            QFrame * {
                background:transparent;
                border:none;
            }
        """)

        ai_msg_l = QVBoxLayout(
            ai_msg
        )

        ai_msg_l.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        overall = self.current_scores.get(
            "overall",
            0,
        )

        try:
            overall = float(overall)
        except Exception:
            overall = 0

        target_level = self.profile.get(
            "target_level",
            TARGET_LEVEL,
        )
        try:
            target_threshold = CEFR_LEVELS[target_level][0]
        except Exception:
            target_threshold = 51

        gap = max(
            0,
            target_threshold - overall,
        )

        weakest = get_weakest_skill(
            self.current_scores,
        )

        self.ai_msg_lbl = QLabel(
            f"You need only +{int(gap)} overall "
            f"to reach {target_level}!\n\n"
            f"{weakest} is your biggest weakness.\n\n"
            f"Let's improve step by step. 💪"
        )

        self.ai_msg_lbl.setWordWrap(
            True
        )

        self.ai_msg_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.ai_msg_lbl.setStyleSheet("""
            QLabel {
                color:#CBD5E1;
                font-size:12px;
                background:transparent;
                border:none;
            }
        """)

        ai_msg_l.addWidget(
            self.ai_msg_lbl
        )

        right_l.addWidget(
            ai_msg
        )

        # ====================================================
        # ASK IFA
        # ====================================================

        chat_title = QLabel(
            "ASK IFA"
        )

        chat_title.setStyleSheet("""
            QLabel {
                color:#3B82F6;
                font-size:11px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
        """)

        right_l.addWidget(
            chat_title
        )

        # ----------------------------------------------------
        # CHAT OUTPUT
        # ----------------------------------------------------

        self.ifa_chat = QTextEdit()

        self.ifa_chat.setReadOnly(
            True
        )

        self.ifa_chat.setPlaceholderText(
            "IFA javoblari shu yerda ko'rinadi..."
        )

        self.ifa_chat.setStyleSheet("""
            QTextEdit {
                background:#0B1220;
                color:#CBD5E1;
                border:1px solid #1E293B;
                border-radius:8px;
                padding:8px;
                font-size:12px;
            }
        """)

        self.ifa_chat.setMinimumHeight(
            150
        )

        right_l.addWidget(
            self.ifa_chat
        )

        # ====================================================
        # INPUT
        # ====================================================

        self.ifa_input = QLineEdit()

        self.ifa_input.setPlaceholderText(
            "IFA'dan biror narsa so'rang..."
        )

        self.ifa_input.setFixedHeight(
            38
        )

        self.ifa_input.setStyleSheet("""
            QLineEdit {
                background:#0F172A;
                color:#F1F5F9;
                border:1px solid #334155;
                border-radius:8px;
                padding:0 12px;
                font-size:12px;
            }

            QLineEdit:focus {
                border:1px solid #3B82F6;
            }
        """)

        right_l.addWidget(
            self.ifa_input
        )

        # ====================================================
        # SEND BUTTON
        # ====================================================

        send_btn = QPushButton(
            "✦  SEND TO IFA"
        )

        send_btn.setFixedHeight(
            38
        )

        send_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        send_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;
                color:white;
                border:none;
                border-radius:8px;
                font-size:11px;
                font-weight:bold;
            }

            QPushButton:hover {
                background:#2563EB;
            }

            QPushButton:pressed {
                background:#1D4ED8;
            }

            QPushButton:disabled {
                background:#334155;
                color:#64748B;
            }
        """)

        self.send_btn = send_btn

        send_btn.clicked.connect(
            self._ask_ifa
        )

        self.ifa_input.returnPressed.connect(
            self._ask_ifa
        )

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(38, 38)
        self.voice_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.voice_btn.setToolTip(
            "Mikrofon orqali IFA bilan gapirish"
        )
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background:#0F172A;
                color:#3B82F6;
                border:1px solid #334155;
                border-radius:8px;
                font-size:16px;
            }
            QPushButton:hover {
                background:#1E293B;
                border:1px solid #3B82F6;
            }
            QPushButton:disabled {
                color:#64748B;
                border-color:#1E293B;
            }
        """)
        self.voice_btn.clicked.connect(
            self._voice_ask
        )

        send_row = QHBoxLayout()
        send_row.setSpacing(8)
        send_row.addWidget(send_btn, 1)
        send_row.addWidget(self.voice_btn)

        right_l.addLayout(send_row)

        # ====================================================
        # PROGRESS
        # ====================================================

        prog_title = QLabel(
            "Your Progress"
        )

        prog_title.setStyleSheet("""
            QLabel {
                font-size:13px;
                font-weight:bold;
                color:#F1F5F9;
                background:transparent;
                border:none;
            }
        """)

        right_l.addWidget(
            prog_title
        )

        self.sidebar_bars = []

        for (
            skill,
            score,
            color,
            _,
        ) in self.skills:

            try:
                pct = int(
                    min(
                        100,
                        (float(score) / 75) * 100,
                    )
                )
            except Exception:
                pct = 0

            row = QHBoxLayout()

            skill_lbl = QLabel(
                skill
            )

            skill_lbl.setFixedWidth(
                80
            )

            skill_lbl.setStyleSheet("""
                QLabel {
                    color:#94A3B8;
                    font-size:12px;
                    background:transparent;
                    border:none;
                }
            """)

            bar = QProgressBar()

            bar.setValue(
                pct
            )

            bar.setTextVisible(
                False
            )

            bar.setFixedHeight(
                6
            )

            bar.setStyleSheet(
                f"""
                QProgressBar {{
                    background:#1E293B;
                    border-radius:3px;
                    border:none;
                }}

                QProgressBar::chunk {{
                    background:{color};
                    border-radius:3px;
                }}
                """
            )

            pct_lbl = QLabel(
                f"{pct}%"
            )

            pct_lbl.setFixedWidth(
                35
            )

            pct_lbl.setStyleSheet("""
                QLabel {
                    color:#94A3B8;
                    font-size:11px;
                    background:transparent;
                    border:none;
                }
            """)

            row.addWidget(
                skill_lbl
            )

            row.addWidget(
                bar,
                1,
            )

            row.addWidget(
                pct_lbl
            )

            right_l.addLayout(
                row
            )

            self.sidebar_bars.append(
                (bar, pct_lbl)
            )

        right_l.addStretch()

        # ====================================================
        # FINAL
        # ====================================================

        main.addWidget(
            self.left_scroll,
            1,
        )

        main.addWidget(
            right
        )


# ============================================================
# HELPERS
# ============================================================

    SKILL_PAGES = {
        "Speaking": "Speaking",
        "Writing": "Writing",
        "Reading": "Reading",
        "Listening": "Listening",
        "Vocabulary": "Vocabulary",
    }

    def _populate_score_cards(self):
        while self.scores_row.count():
            item = self.scores_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.current_scores = get_current_scores(self.db)
        plan_mins = minutes_by_skill(self.today_tasks)

        self.skills = [
            (
                "Reading",
                self.current_scores.get("reading", 0),
                "#10B981",
                plan_mins["Reading"],
            ),
            (
                "Listening",
                self.current_scores.get("listening", 0),
                "#8B5CF6",
                plan_mins["Listening"],
            ),
            (
                "Speaking",
                self.current_scores.get("speaking", 0),
                "#3B82F6",
                plan_mins["Speaking"],
            ),
            (
                "Writing",
                self.current_scores.get("writing", 0),
                "#C084FC",
                plan_mins["Writing"],
            ),
        ]

        for skill, score, color, mins in self.skills:
            self.scores_row.addWidget(
                ScoreCard(skill, score, color, mins)
            )

        self._refresh_sidebar_progress()

    def _refresh_sidebar_progress(self):
        if not hasattr(self, "sidebar_bars"):
            return

        for index, (bar, pct_lbl) in enumerate(
            self.sidebar_bars
        ):
            if index >= len(self.skills):
                break

            score = self.skills[index][1]
            try:
                pct = int(
                    min(100, (float(score) / 75) * 100)
                )
            except Exception:
                pct = 0

            bar.setValue(pct)
            pct_lbl.setText(f"{pct}%")

    @staticmethod
    def _escape_html(text):
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )


# ============================================================
# ASK IFA
# ============================================================

    def _ask_ifa(self):

        question = (
            self.ifa_input.text().strip()
        )

        if not question:
            return

        # ----------------------------------------------------
        # CLEAR INPUT
        # ----------------------------------------------------

        self.ifa_input.clear()

        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

        safe_question = self._escape_html(
            question
        )

        self.ifa_chat.append(
            f"<b style='color:#3B82F6;'>"
            f"Siz:</b> "
            f"{safe_question}"
        )

        # ----------------------------------------------------
        # LOADING
        # ----------------------------------------------------

        self.ifa_chat.append(
            "<span style='color:#64748B;'>"
            "IFA o'ylayapti..."
            "</span>"
        )

        # ----------------------------------------------------
        # DISABLE
        # ----------------------------------------------------

        self.send_btn.setEnabled(
            False
        )

        self.voice_btn.setEnabled(
            False
        )

        self.ifa_input.setEnabled(
            False
        )

        # ----------------------------------------------------
        # WORKER
        # ----------------------------------------------------

        def ask():

            try:

                response = self.ai.chat(
                    question
                )

                if not response:

                    response = (
                        "IFA hozircha javob bera olmadi."
                    )

                self.signals.ai_response.emit(
                    response
                )

            except Exception as e:

                self.signals.ai_response.emit(
                    f"IFA xatosi: {e}"
                )

        threading.Thread(
            target=ask,
            daemon=True,
        ).start()


    def _voice_ask(self):

        if not self.voice_assistant:
            self.signals.ai_response.emit(
                "Voice assistant ulanmagan."
            )
            return

        self.ifa_chat.append(
            "<span style='color:#64748B;'>"
            "🎤 Tinglayapman..."
            "</span>"
        )

        self.send_btn.setEnabled(False)
        self.voice_btn.setEnabled(False)
        self.ifa_input.setEnabled(False)

        def on_response(response):
            self.signals.ai_response.emit(response)

        def on_error(message):
            self.signals.ai_response.emit(message)

        self.voice_assistant.on_response = on_response
        self.voice_assistant.on_error = on_error
        self.voice_assistant.listen_and_process()


# ============================================================
# SHOW AI RESPONSE
# ============================================================

    def _show_ai_response(
        self,
        response,
    ):

        # ----------------------------------------------------
        # REMOVE LOADING
        # ----------------------------------------------------

        current = self.ifa_chat.toHtml()

        if (
            "IFA o'ylayapti..." in current
            or "Tinglayapman" in current
        ):

            cursor = self.ifa_chat.textCursor()

            cursor.movePosition(
                cursor.MoveOperation.End
            )

            cursor.select(
                cursor.SelectionType.BlockUnderCursor
            )

            cursor.removeSelectedText()

            cursor.deletePreviousChar()

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        safe_response = (
            str(response)
            .replace(
                "&",
                "&amp;",
            )
            .replace(
                "<",
                "&lt;",
            )
            .replace(
                ">",
                "&gt;",
            )
            .replace(
                "\n",
                "<br>",
            )
        )

        self.ifa_chat.append(
            f"<b style='color:#10B981;'>"
            f"IFA:</b> "
            f"{safe_response}"
        )

        # ----------------------------------------------------
        # ENABLE
        # ----------------------------------------------------

        self.send_btn.setEnabled(
            True
        )

        self.voice_btn.setEnabled(
            True
        )

        self.ifa_input.setEnabled(
            True
        )

        self.ifa_input.setFocus()

        # ----------------------------------------------------
        # SCROLL DOWN
        # ----------------------------------------------------

        scrollbar = (
            self.ifa_chat.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )


# ============================================================
# LOAD DATA
# ============================================================

    def _load_data(self):
        self._load_generation += 1
        generation = self._load_generation

        def run():
            try:

                # ------------------------------------------------
                # TODAY PLAN
                # ------------------------------------------------

                plan = (
                    self.db.get_today_plan()
                )

                if plan:
                    plan = [
                        task for task in plan
                        if task.get("skill") in EXAM_SKILL_LABELS
                    ]

                if not plan:

                    from src.smart_planner import (
                        SmartPlanner
                    )

                    planner = SmartPlanner(
                        self.db,
                        self.ai,
                    )

                    goal = (
                        planner.load_goal()
                    )

                    if goal:

                        planner.update_daily_tasks(
                            goal
                        )

                        plan = (
                            self.db.get_today_plan()
                        )

                # ------------------------------------------------
                # FALLBACK PLAN
                # ------------------------------------------------

                if not plan:

                    plan = (
                        self._default_plan()
                    )

                if generation != self._load_generation:
                    return

                if not hasattr(self, "signals"):
                    return

                self.signals.plan_loaded.emit(
                    {
                        "tasks": plan
                    }
                )

                # ------------------------------------------------
                # GOAL
                # ------------------------------------------------

                from src.smart_planner import (
                    SmartPlanner
                )

                planner = SmartPlanner(
                    self.db,
                    self.ai,
                )

                goal = (
                    planner.load_goal()
                )

                if generation != self._load_generation:
                    return

                if goal:

                    self.signals.goal_loaded.emit(
                        goal
                    )

            except RuntimeError:
                return

            except Exception as e:

                print(
                    f"Dashboard load xato: {e}"
                )

                if generation != self._load_generation:
                    return

                if not hasattr(self, "signals"):
                    return

                self.signals.plan_loaded.emit(
                    {
                        "tasks":
                        self._default_plan()
                    }
                )

        threading.Thread(
            target=run,
            daemon=True,
        ).start()


# ============================================================
# DEFAULT PLAN
# ============================================================

    def _default_plan(self):

        return [

            {
                "skill": "Speaking",
                "duration_minutes": 25,
                "task_type": "practice",
                "is_completed": 0,
            },

            {
                "skill": "Writing",
                "duration_minutes": 19,
                "task_type": "essay",
                "is_completed": 0,
            },

            {
                "skill": "Listening",
                "duration_minutes": 16,
                "task_type": "practice",
                "is_completed": 0,
            },

            {
                "skill": "Reading",
                "duration_minutes": 18,
                "task_type": "practice",
                "is_completed": 0,
            },
        ]


# ============================================================
# UPDATE MISSION
# ============================================================

    def _update_mission(
        self,
        data,
    ):

        tasks = data.get(
            "tasks",
            [],
        )

        self.today_tasks = tasks
        self._populate_score_cards()

        # ----------------------------------------------------
        # REMOVE OLD MISSION
        # ----------------------------------------------------

        idx = self.left_l.indexOf(
            self.mission_slot
        )

        if idx >= 0:

            self.left_l.removeWidget(
                self.mission_slot
            )

            self.mission_slot.deleteLater()

        # ----------------------------------------------------
        # NEW MISSION
        # ----------------------------------------------------

        self.mission_slot = MissionCard(
            tasks,
            self._start_session,
            level=self.display_level,
        )

        # ----------------------------------------------------
        # INSERT BEFORE STRETCH
        # ----------------------------------------------------

        insert_at = (
            self.left_l.count() - 1
        )

        self.left_l.insertWidget(
            max(
                0,
                insert_at,
            ),
            self.mission_slot,
        )


# ============================================================
# UPDATE GOAL
# ============================================================

    def _update_goal(
        self,
        goal_data,
    ):

        # ----------------------------------------------------
        # REMOVE OLD GOAL
        # ----------------------------------------------------

        idx = self.left_l.indexOf(
            self.goal_slot
        )

        if idx >= 0:

            self.left_l.removeWidget(
                self.goal_slot
            )

            self.goal_slot.deleteLater()

        # ----------------------------------------------------
        # NEW GOAL
        # ----------------------------------------------------

        self.goal_slot = GoalProgressCard(
            goal_data,
            db=self.db,
        )

        self.display_level = goal_data.get(
            "target_level",
            TARGET_LEVEL,
        )

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        self.left_l.insertWidget(
            3,
            self.goal_slot,
        )

        # ----------------------------------------------------
        # UPDATE AI MESSAGE
        # ----------------------------------------------------

        daily = goal_data.get(
            "daily_plan",
            {},
        )

        weakest = get_weakest_skill(
            self.current_scores,
            self.db,
        ).lower()

        focus_min = daily.get(
            weakest,
            daily.get("speaking", 25),
        )

        target = goal_data.get(
            "target_level",
            TARGET_LEVEL,
        )

        days = goal_data.get(
            "days",
            60,
        )

        self.ai_msg_lbl.setText(
            f"Maqsad: {target} — "
            f"{days} kun ichida!\n\n"
            f"{weakest.title()} eng zaif skill.\n"
            f"Bugun {focus_min} min "
            f"{weakest.title()} mashq qiling. 💪"
        )


# ============================================================
# START SESSION
# ============================================================

    def _start_session(self):

        next_task = None

        for task in self.today_tasks:
            if task.get("is_completed"):
                continue
            if task.get("skill") not in EXAM_SKILL_LABELS:
                continue
            next_task = task
            break

        if next_task and self.on_start_task:
            self.on_start_task(next_task)

        def run_voice():
            try:
                if not self.voice_assistant:
                    return

                response = (
                    self.voice_assistant
                    .process_command(
                        "Bugungi darsni boshlaymiz"
                    )
                )

                if response:
                    self.signals.ai_response.emit(
                        response
                    )

            except Exception as e:
                self.signals.ai_response.emit(
                    f"Session xatosi: {e}"
                )

        threading.Thread(
            target=run_voice,
            daemon=True,
        ).start()


# ============================================================
# REFRESH
# ============================================================

    def _profile_subtitle(self):
        current = self.profile.get(
            "current_level",
            "B1",
        )
        target = self.profile.get(
            "target_level",
            TARGET_LEVEL,
        )
        daily = self.profile.get(
            "daily_minutes",
            90,
        )
        return (
            f"Maqsad: {current} → {target} | "
            f"Kunlik {daily} daqiqa mashq | "
            f"Faqat 4 ta imtihon skilli"
        )

    def refresh(self):

        self.profile = get_profile(self.db)
        self.display_level = self.profile.get(
            "target_level",
            TARGET_LEVEL,
        )

        if hasattr(self, "greet_lbl"):
            hour = datetime.now().hour
            if hour < 12:
                greeting = "Good morning"
            elif hour >= 18:
                greeting = "Good evening"
            else:
                greeting = "Good afternoon"

            self.greet_lbl.setText(
                f"{greeting}, "
                f"{self.profile['name']}! 👋"
            )

        if hasattr(self, "sub_lbl"):
            self.sub_lbl.setText(
                self._profile_subtitle()
            )

        if self.voice_assistant:
            self.voice_assistant.user_name = self.profile["name"]

        self.current_scores = get_current_scores(
            self.db
        )
        self._populate_score_cards()
        self._load_data()
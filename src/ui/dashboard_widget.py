from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
from src.ui.styles import SKILL_COLORS, COLORS
from config.settings import USER_NAME, CURRENT_SCORES, CEFR_LEVELS

class ScoreCard(QFrame):
    """Har bir skill uchun kichik karta"""
    def __init__(self, skill, score, color, today_min=0):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
                padding: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Skill nomi
        name_lbl = QLabel(skill)
        name_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: bold;"
        )
        layout.addWidget(name_lbl)

        # Ball
        score_lbl = QLabel(f"{score}%")
        score_lbl.setStyleSheet(
            "color: #F1F5F9; font-size: 26px; font-weight: bold;"
        )
        layout.addWidget(score_lbl)

        # Progress bar
        bar = QProgressBar()
        bar.setValue(score)
        bar.setTextVisible(False)
        bar.setFixedHeight(4)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1E293B;
                border-radius: 2px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(bar)

        # Bugungi darslar
        today_lbl = QLabel(f"Bugungi dars  {today_min} min")
        today_lbl.setStyleSheet(
            "color: #475569; font-size: 10px;"
        )
        layout.addWidget(today_lbl)


class MissionCard(QFrame):
    """Today's Mission kartasi"""
    def __init__(self, tasks, on_start):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame {
                background-color: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("TODAY'S MISSION")
        title.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )
        total_time = sum(t.get("duration_minutes", 0) for t in tasks)
        time_lbl = QLabel(f"⏱  {total_time} min")
        time_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(time_lbl)
        layout.addLayout(header)

        # Tasks
        skill_icons = {
            "Listening":  ("🎧", "#8B5CF6"),
            "Reading":    ("📖", "#10B981"),
            "Speaking":   ("🎤", "#3B82F6"),
            "Writing":    ("✍️",  "#C084FC"),
            "Vocabulary": ("📚", "#4ADE80")
        }

        for task in tasks[:4]:
            skill = task.get("skill", "")
            icon, color = skill_icons.get(skill, ("📄", "#94A3B8"))
            duration = task.get("duration_minutes", 0)
            task_type = task.get("task_type", "")
            completed = task.get("is_completed", 0)

            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: #0F172A;
                    border-radius: 8px;
                    border: 1px solid #1E293B;
                }
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)

            # Icon circle
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                f"font-size: 18px; background-color: {color}22;"
                f"border-radius: 16px; padding: 4px 8px;"
            )

            # Info
            info = QVBoxLayout()
            skill_lbl = QLabel(f"{skill} — B2")
            skill_lbl.setStyleSheet(
                "color: #F1F5F9; font-size: 13px; font-weight: bold;"
            )
            type_lbl = QLabel(task_type.replace("_", " ").title())
            type_lbl.setStyleSheet(
                "color: #94A3B8; font-size: 11px;"
            )
            info.addWidget(skill_lbl)
            info.addWidget(type_lbl)
            info.setSpacing(2)

            # Duration + arrow
            dur_lbl = QLabel(f"{duration} min  ›")
            dur_lbl.setStyleSheet(
                "color: #94A3B8; font-size: 12px;"
            )

            row_layout.addWidget(icon_lbl)
            row_layout.addLayout(info)
            row_layout.addStretch()
            row_layout.addWidget(dur_lbl)
            layout.addWidget(row)

        # Start button
        start_btn = QPushButton("▶  START SESSION")
        start_btn.setObjectName("btn_primary")
        start_btn.setFixedHeight(42)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563EB; }
            QPushButton:pressed { background-color: #1D4ED8; }
        """)
        start_btn.clicked.connect(on_start)
        layout.addWidget(start_btn)


class DashboardWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self._build()

    def _build(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── CHAP: Asosiy kontent ──
        left = QWidget()
        left.setStyleSheet("background-color: #0A0F1E;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(28, 24, 20, 24)
        left_layout.setSpacing(20)

        # Salomlashuv
        hour = datetime.now().hour
        greeting = (
            "Good morning" if hour < 12
            else "Good evening" if hour >= 18
            else "Good afternoon"
        )
        greet_layout = QHBoxLayout()
        greet_lbl = QLabel(f"{greeting}, {USER_NAME}! 👋")
        greet_lbl.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #F1F5F9;"
        )
        greet_layout.addWidget(greet_lbl)
        greet_layout.addStretch()
        left_layout.addLayout(greet_layout)

        sub_lbl = QLabel(
            "I've analyzed your progress. "
            "Here's what we should work on today."
        )
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        left_layout.addWidget(sub_lbl)

        # Score cards
        scores_layout = QGridLayout()
        scores_layout.setSpacing(12)

        skills = [
            ("Reading",    CURRENT_SCORES["reading"],    "#10B981", 18),
            ("Listening",  CURRENT_SCORES["listening"],  "#8B5CF6", 15),
            ("Speaking",   CURRENT_SCORES["speaking"],   "#3B82F6", 10),
            ("Writing",    CURRENT_SCORES["writing"],    "#C084FC", 20),
        ]

        for i, (skill, score, color, mins) in enumerate(skills):
            # Score ni 75 dan foizga o'tkazish
            pct = int((score / 75) * 100)
            card = ScoreCard(skill, pct, color, mins)
            scores_layout.addWidget(card, 0, i)

        left_layout.addLayout(scores_layout)

        # Today's Mission
        today_plan = self.db.get_today_plan()
        if not today_plan:
            today_plan = [
                {"skill": "Listening",  "duration_minutes": 15,
                 "task_type": "B2 practice"},
                {"skill": "Vocabulary", "duration_minutes": 10,
                 "task_type": "review & practice"},
                {"skill": "Reading",    "duration_minutes": 15,
                 "task_type": "Part 3 academic"},
            ]

        mission = MissionCard(today_plan, self._start_session)
        left_layout.addWidget(mission)
        left_layout.addStretch()

        # ── O'NG: AI Panel ──
        right = QWidget()
        right.setFixedWidth(300)
        right.setStyleSheet(
            "background-color: #0F172A;"
            "border-left: 1px solid #1E293B;"
        )
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 24, 20, 24)
        right_layout.setSpacing(16)

        # IFA Mentor AI
        ai_header = QHBoxLayout()
        ai_icon = QLabel("⬡")
        ai_icon.setStyleSheet(
            "font-size: 18px; color: #3B82F6;"
        )
        ai_title = QLabel("IFA Mentor")
        ai_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #F1F5F9;"
        )
        ai_dot = QLabel("● AI")
        ai_dot.setStyleSheet(
            "font-size: 11px; color: #10B981;"
        )
        ai_header.addWidget(ai_icon)
        ai_header.addWidget(ai_title)
        ai_header.addStretch()
        ai_header.addWidget(ai_dot)
        right_layout.addLayout(ai_header)

        # AI message
        ai_msg = QFrame()
        ai_msg.setStyleSheet("""
            QFrame {
                background-color: #131C31;
                border-radius: 10px;
                border: 1px solid #1E293B;
            }
        """)
        ai_msg_layout = QVBoxLayout(ai_msg)
        ai_msg_layout.setContentsMargins(14, 12, 14, 12)

        overall = CURRENT_SCORES["overall"]
        gap = max(0, CEFR_LEVELS["B2"][0] - overall)

        msg_text = QLabel(
            f"You need only +{gap} overall to reach B2!\n\n"
            f"Speaking is your biggest weakness.\n\n"
            f"Let's improve step by step. 💪"
        )
        msg_text.setStyleSheet(
            "color: #CBD5E1; font-size: 12px; line-height: 1.5;"
        )
        msg_text.setWordWrap(True)
        ai_msg_layout.addWidget(msg_text)
        right_layout.addWidget(ai_msg)

        # Ask button
        ask_btn = QPushButton("✦  ASK IFA ANYTHING")
        ask_btn.setFixedHeight(40)
        ask_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ask_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        right_layout.addWidget(ask_btn)

        # Progress bars
        progress_title = QLabel("Your Progress")
        progress_title.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #F1F5F9;"
        )
        right_layout.addWidget(progress_title)

        for skill, score, color, _ in skills:
            pct = int((score / 75) * 100)
            row = QHBoxLayout()
            lbl = QLabel(skill)
            lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
            lbl.setFixedWidth(80)

            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #1E293B;
                    border-radius: 3px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)

            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setStyleSheet(
                "color: #94A3B8; font-size: 11px;"
            )
            pct_lbl.setFixedWidth(35)

            row.addWidget(lbl)
            row.addWidget(bar)
            row.addWidget(pct_lbl)
            right_layout.addLayout(row)

        right_layout.addStretch()

        main_layout.addWidget(left, 1)
        main_layout.addWidget(right)

    def _start_session(self):
        print("▶ Session boshlandi!")

    def refresh(self):
        pass


# Test
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    w = DashboardWidget(db, ai)
    w.resize(1100, 700)
    w.show()
    sys.exit(app.exec())
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QProgressBar, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from datetime import datetime
from config.settings import (
    USER_NAME, CURRENT_SCORES, CEFR_LEVELS
)


class DashboardSignals(QObject):
    plan_loaded = pyqtSignal(dict)
    goal_loaded = pyqtSignal(dict)


class ScoreCard(QFrame):
    def __init__(self, skill, score, color, today_min=0):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        name_lbl = QLabel(skill)
        name_lbl.setStyleSheet(
            f"color:{color};font-size:11px;"
            "font-weight:bold;border:none;"
        )
        layout.addWidget(name_lbl)

        pct = int((score / 75) * 100)
        score_lbl = QLabel(f"{pct}%")
        score_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:26px;"
            "font-weight:bold;border:none;"
        )
        layout.addWidget(score_lbl)

        bar = QProgressBar()
        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setFixedHeight(4)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background:#1E293B;
                border-radius:2px;
                border:none;
            }}
            QProgressBar::chunk {{
                background:{color};
                border-radius:2px;
            }}
        """)
        layout.addWidget(bar)

        today_lbl = QLabel(f"Bugungi dars  {today_min} min")
        today_lbl.setStyleSheet(
            "color:#475569;font-size:10px;border:none;"
        )
        layout.addWidget(today_lbl)


class MissionCard(QFrame):
    def __init__(self, tasks, on_start):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)

        # Height is allowed to grow with the number of tasks.
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()

        title = QLabel("TODAY'S MISSION")
        title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )

        total_time = sum(
            t.get("duration_minutes", 0)
            for t in tasks
        )

        time_lbl = QLabel(f"⏱  {total_time} min")
        time_lbl.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(time_lbl)
        layout.addLayout(header)

        skill_icons = {
            "Listening": ("🎧", "#8B5CF6"),
            "Reading": ("📖", "#10B981"),
            "Speaking": ("🎤", "#3B82F6"),
            "Writing": ("✍️", "#C084FC"),
            "Vocabulary": ("📚", "#4ADE80")
        }

        # IMPORTANT:
        # Do not limit this to tasks[:5].
        # All tasks are displayed; if the dashboard is short,
        # the left-side scrollbar lets the user reach them.
        for task in tasks:
            skill = task.get("skill", "")
            icon, color = skill_icons.get(
                skill, ("📄", "#94A3B8")
            )

            duration = task.get("duration_minutes", 0)
            task_type = task.get("task_type", "")
            completed = task.get("is_completed", 0)

            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background:#0F172A;
                    border-radius:8px;
                    border:1px solid #1E293B;
                }
            """)

            row.setMinimumHeight(52)
            row.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )

            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(12, 7, 12, 7)
            row_l.setSpacing(10)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                "font-size:18px;"
                "border:none;"
                "background:transparent;"
                "padding:0 6px;"
            )
            icon_lbl.setFixedWidth(34)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            info_l = QVBoxLayout()
            info_l.setSpacing(2)

            skill_lbl = QLabel(f"{skill} — B2")
            skill_lbl.setStyleSheet(
                "color:#F1F5F9;"
                "font-size:13px;"
                "font-weight:bold;"
                "border:none;"
                "background:transparent;"
            )
            skill_lbl.setMinimumHeight(17)
            skill_lbl.setAlignment(
                Qt.AlignmentFlag.AlignVCenter |
                Qt.AlignmentFlag.AlignLeft
            )

            type_lbl = QLabel(
                task_type.replace("_", " ").title()
            )
            type_lbl.setStyleSheet(
                "color:#94A3B8;"
                "font-size:11px;"
                "border:none;"
                "background:transparent;"
            )
            type_lbl.setMinimumHeight(15)
            type_lbl.setAlignment(
                Qt.AlignmentFlag.AlignVCenter |
                Qt.AlignmentFlag.AlignLeft
            )

            info_l.addWidget(skill_lbl)
            info_l.addWidget(type_lbl)

            status_lbl = QLabel(
                "✅" if completed else f"{duration} min  ›"
            )
            status_lbl.setStyleSheet(
                f"color:{'#10B981' if completed else '#94A3B8'};"
                "font-size:12px;"
                "border:none;"
            )

            row_l.addWidget(icon_lbl)
            row_l.addLayout(info_l)
            row_l.addStretch()
            row_l.addWidget(status_lbl)

            layout.addWidget(row)

        start_btn = QPushButton("▶  START SESSION")
        start_btn.setFixedHeight(42)
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
        """)
        start_btn.clicked.connect(on_start)
        layout.addWidget(start_btn)


class GoalProgressCard(QFrame):
    def __init__(self, goal_data):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E3A5F;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()

        title = QLabel("🎯 MAQSAD PROGRESSI")
        title.setStyleSheet(
            "color:#10B981;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )

        target = goal_data.get("target_level", "B2")
        end_date = goal_data.get("end_date", "")

        date_lbl = QLabel(f"{target} → {end_date}")
        date_lbl.setStyleSheet(
            "color:#475569;font-size:11px;"
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(date_lbl)
        layout.addLayout(header)

        current = CURRENT_SCORES["overall"]
        target_score = goal_data.get("target_overall", 51)

        prog_row = QHBoxLayout()

        prog_lbl = QLabel(f"{current}/75")
        prog_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:13px;"
            "font-weight:bold;"
        )

        target_lbl = QLabel(f"→ {target_score}/75")
        target_lbl.setStyleSheet(
            "color:#10B981;font-size:13px;"
            "font-weight:bold;"
        )

        prog_row.addWidget(prog_lbl)
        prog_row.addStretch()
        prog_row.addWidget(target_lbl)
        layout.addLayout(prog_row)

        prog_bar = QProgressBar()
        prog_bar.setValue(0)
        prog_bar.setTextVisible(False)
        prog_bar.setFixedHeight(8)
        prog_bar.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:4px;
                border:none;
            }
            QProgressBar::chunk {
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #3B82F6,
                    stop:1 #10B981
                );
                border-radius:4px;
            }
        """)
        layout.addWidget(prog_bar)

        milestones = goal_data.get("milestones", [])

        if milestones:
            mile_row = QHBoxLayout()
            mile_row.setSpacing(6)

            for m in milestones:
                reached = m.get("reached", False)

                mf = QFrame()
                mf.setStyleSheet(f"""
                    QFrame {{
                        background:{
                            '#0F2A1E' if reached
                            else '#0F172A'
                        };
                        border-radius:6px;
                        border:1px solid {
                            '#10B981' if reached
                            else '#1E293B'
                        };
                    }}
                """)

                ml = QVBoxLayout(mf)
                ml.setContentsMargins(8, 4, 8, 4)
                ml.setSpacing(1)

                pl = QLabel(m["label"])
                pl.setStyleSheet(
                    f"color:{'#10B981' if reached else '#475569'};"
                    "font-size:10px;"
                    "font-weight:bold;"
                    "border:none;"
                )
                pl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                parts = m["date"].split(".")
                short_date = f"{parts[0]}.{parts[1]}"

                dl = QLabel(short_date)
                dl.setStyleSheet(
                    "color:#334155;"
                    "font-size:9px;"
                    "border:none;"
                )
                dl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                ml.addWidget(pl)
                ml.addWidget(dl)
                mile_row.addWidget(mf)

            layout.addLayout(mile_row)

        daily_gain = goal_data.get("daily_gain_needed", 0)
        days = goal_data.get("days", 60)

        gain_lbl = QLabel(
            f"Kuniga +{daily_gain} ball kerak  •  "
            f"{days} kun"
        )
        gain_lbl.setStyleSheet(
            "color:#475569;font-size:11px;"
        )
        layout.addWidget(gain_lbl)


class DashboardWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()

        self.db = db
        self.ai = ai

        self.signals = DashboardSignals()
        self.signals.plan_loaded.connect(
            self._update_mission
        )
        self.signals.goal_loaded.connect(
            self._update_goal
        )

        self._build()
        self._load_data()

    def _build(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # =====================================================
        # CHAP TOMON
        # =====================================================

        left_content = QWidget()
        left_content.setStyleSheet(
            "background:#0A0F1E;"
        )

        self.left_l = QVBoxLayout(left_content)
        self.left_l.setContentsMargins(
            28, 24, 20, 24
        )
        self.left_l.setSpacing(12)

        hour = datetime.now().hour

        greeting = (
            "Good morning" if hour < 12
            else "Good evening" if hour >= 18
            else "Good afternoon"
        )

        greet_lbl = QLabel(
            f"{greeting}, {USER_NAME}! 👋"
        )
        greet_lbl.setStyleSheet(
            "font-size:24px;"
            "font-weight:bold;"
            "color:#F1F5F9;"
        )
        self.left_l.addWidget(greet_lbl)

        sub_lbl = QLabel(
            "I've analyzed your progress. "
            "Here's what we should work on today."
        )
        sub_lbl.setStyleSheet(
            "color:#94A3B8;font-size:13px;"
        )
        self.left_l.addWidget(sub_lbl)

        # =====================================================
        # SCORE CARDS
        # =====================================================

        scores_l = QHBoxLayout()
        scores_l.setSpacing(12)

        self.skills = [
            (
                "Reading",
                CURRENT_SCORES["reading"],
                "#10B981",
                18
            ),
            (
                "Listening",
                CURRENT_SCORES["listening"],
                "#8B5CF6",
                15
            ),
            (
                "Speaking",
                CURRENT_SCORES["speaking"],
                "#3B82F6",
                10
            ),
            (
                "Writing",
                CURRENT_SCORES["writing"],
                "#C084FC",
                20
            ),
        ]

        for skill, score, color, mins in self.skills:
            card = ScoreCard(
                skill,
                score,
                color,
                mins
            )
            scores_l.addWidget(card)

        self.left_l.addLayout(scores_l)

        # =====================================================
        # GOAL PLACEHOLDER
        # =====================================================

        self.goal_slot = QFrame()
        self.goal_slot.setFixedHeight(0)
        self.left_l.addWidget(self.goal_slot)

        # =====================================================
        # MISSION PLACEHOLDER
        # =====================================================

        self.mission_slot = QFrame()
        self.mission_slot.setMinimumHeight(100)
        self.mission_slot.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        self.mission_slot.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)

        mp_l = QVBoxLayout(self.mission_slot)
        mp_l.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        loading = QLabel(
            "⏳ Kunlik reja yuklanmoqda..."
        )
        loading.setStyleSheet(
            "color:#475569;"
            "font-size:13px;"
            "border:none;"
        )
        loading.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        mp_l.addWidget(loading)
        self.left_l.addWidget(self.mission_slot)

        self.left_l.addStretch()

        # =====================================================
        # CHAP TOMON UCHUN SCROLL
        #
        # Dashboard balandligi kichik bo'lsa ham:
        # Reading / Listening / Speaking / Writing /
        # Vocabulary / Today's Mission / Goal
        # yo'qolib ketmaydi.
        # =====================================================

        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
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
                margin:4px 2px 4px 0;
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

        # =====================================================
        # O'NG PANEL
        # =====================================================

        right = QWidget()
        right.setFixedWidth(300)
        right.setStyleSheet(
            "background:#0F172A;"
            "border-left:1px solid #1E293B;"
        )

        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(
            20, 24, 20, 24
        )
        right_l.setSpacing(16)

        ai_header = QHBoxLayout()

        ai_icon = QLabel("⬡")
        ai_icon.setStyleSheet(
            "font-size:18px;color:#3B82F6;"
        )

        ai_title = QLabel("IFA Mentor")
        ai_title.setStyleSheet(
            "font-size:14px;"
            "font-weight:bold;"
            "color:#F1F5F9;"
        )

        ai_dot = QLabel("● AI")
        ai_dot.setStyleSheet(
            "font-size:11px;color:#10B981;"
        )

        ai_header.addWidget(ai_icon)
        ai_header.addWidget(ai_title)
        ai_header.addStretch()
        ai_header.addWidget(ai_dot)

        right_l.addLayout(ai_header)

        ai_msg = QFrame()
        ai_msg.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)

        ai_msg_l = QVBoxLayout(ai_msg)
        ai_msg_l.setContentsMargins(
            14, 12, 14, 12
        )

        overall = CURRENT_SCORES["overall"]
        gap = max(
            0,
            CEFR_LEVELS["B2"][0] - overall
        )

        self.ai_msg_lbl = QLabel(
            f"You need only +{gap} overall "
            f"to reach B2!\n\n"
            f"Speaking is your biggest weakness.\n\n"
            f"Let's improve step by step. 💪"
        )

        self.ai_msg_lbl.setStyleSheet(
            "color:#CBD5E1;"
            "font-size:12px;"
            "border:none;"
        )
        self.ai_msg_lbl.setWordWrap(True)

        ai_msg_l.addWidget(
            self.ai_msg_lbl
        )
        right_l.addWidget(ai_msg)

        ask_btn = QPushButton(
            "✦  ASK IFA ANYTHING"
        )
        ask_btn.setFixedHeight(40)
        ask_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        ask_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;
                color:white;
                border:none;
                border-radius:8px;
                font-size:12px;
                font-weight:bold;
            }

            QPushButton:hover {
                background:#2563EB;
            }
        """)

        right_l.addWidget(ask_btn)

        prog_title = QLabel(
            "Your Progress"
        )
        prog_title.setStyleSheet(
            "font-size:13px;"
            "font-weight:bold;"
            "color:#F1F5F9;"
        )
        right_l.addWidget(prog_title)

        for skill, score, color, _ in self.skills:
            pct = int((score / 75) * 100)

            row = QHBoxLayout()

            skill_lbl = QLabel(skill)
            skill_lbl.setStyleSheet(
                "color:#94A3B8;"
                "font-size:12px;"
            )
            skill_lbl.setFixedWidth(80)

            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)

            bar.setStyleSheet(f"""
                QProgressBar {{
                    background:#1E293B;
                    border-radius:3px;
                    border:none;
                }}

                QProgressBar::chunk {{
                    background:{color};
                    border-radius:3px;
                }}
            """)

            pct_lbl = QLabel(
                f"{pct}%"
            )
            pct_lbl.setStyleSheet(
                "color:#94A3B8;"
                "font-size:11px;"
            )
            pct_lbl.setFixedWidth(35)

            row.addWidget(skill_lbl)
            row.addWidget(bar)
            row.addWidget(pct_lbl)

            right_l.addLayout(row)

        # =====================================================
        # HAFTALIK JADVAL
        # =====================================================

        self.weekly_frame = QFrame()
        self.weekly_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        self.weekly_frame.hide()

        weekly_l = QVBoxLayout(
            self.weekly_frame
        )
        weekly_l.setContentsMargins(
            14, 12, 14, 12
        )
        weekly_l.setSpacing(6)

        weekly_title = QLabel(
            "HAFTALIK JADVAL"
        )
        weekly_title.setStyleSheet(
            "color:#F59E0B;"
            "font-size:10px;"
            "font-weight:bold;"
            "letter-spacing:1px;"
        )
        weekly_l.addWidget(
            weekly_title
        )

        self.weekly_content_l = QVBoxLayout()
        self.weekly_content_l.setSpacing(4)

        weekly_l.addLayout(
            self.weekly_content_l
        )
        right_l.addWidget(
            self.weekly_frame
        )

        right_l.addStretch()

        # =====================================================
        # FINAL LAYOUT
        # =====================================================

        main.addWidget(
            self.left_scroll,
            1
        )
        main.addWidget(right)

    # =========================================================
    # DATA YUKLASH
    # =========================================================

    def _load_data(self):
        def run():
            try:
                plan = self.db.get_today_plan()

                if not plan:
                    from src.smart_planner import SmartPlanner

                    planner = SmartPlanner(
                        self.db,
                        self.ai
                    )

                    goal = planner.load_goal()

                    if goal:
                        planner.update_daily_tasks(
                            goal
                        )
                        plan = self.db.get_today_plan()

                if not plan:
                    plan = self._default_plan()

                self.signals.plan_loaded.emit(
                    {"tasks": plan}
                )

                from src.smart_planner import SmartPlanner

                planner = SmartPlanner(
                    self.db,
                    self.ai
                )

                goal = planner.load_goal()

                if goal:
                    self.signals.goal_loaded.emit(
                        goal
                    )

            except Exception as e:
                print(
                    f"Dashboard load xato: {e}"
                )

                self.signals.plan_loaded.emit(
                    {
                        "tasks":
                        self._default_plan()
                    }
                )

        threading.Thread(
            target=run,
            daemon=True
        ).start()

    def _default_plan(self):
        return [
            {
                "skill": "Speaking",
                "duration_minutes": 25,
                "task_type": "practice",
                "is_completed": 0
            },
            {
                "skill": "Writing",
                "duration_minutes": 19,
                "task_type": "essay",
                "is_completed": 0
            },
            {
                "skill": "Listening",
                "duration_minutes": 16,
                "task_type": "practice",
                "is_completed": 0
            },
            {
                "skill": "Reading",
                "duration_minutes": 18,
                "task_type": "practice",
                "is_completed": 0
            },
            {
                "skill": "Vocabulary",
                "duration_minutes": 18,
                "task_type": "review",
                "is_completed": 0
            },
        ]

    # =========================================================
    # UPDATE
    # =========================================================

    def _update_mission(self, data):
        tasks = data.get(
            "tasks",
            []
        )

        idx = self.left_l.indexOf(
            self.mission_slot
        )

        if idx >= 0:
            self.left_l.removeWidget(
                self.mission_slot
            )
            self.mission_slot.deleteLater()

        self.mission_slot = MissionCard(
            tasks,
            self._start_session
        )

        insert_at = (
            self.left_l.count() - 1
        )

        self.left_l.insertWidget(
            max(0, insert_at),
            self.mission_slot
        )

    def _update_goal(self, goal_data):
        idx = self.left_l.indexOf(
            self.goal_slot
        )

        if idx >= 0:
            self.left_l.removeWidget(
                self.goal_slot
            )
            self.goal_slot.deleteLater()

        self.goal_slot = GoalProgressCard(
            goal_data
        )

        self.left_l.insertWidget(
            3,
            self.goal_slot
        )

        schedule = goal_data.get(
            "weekly_schedule",
            {}
        )

        if schedule:
            self._update_weekly(
                schedule
            )

        daily = goal_data.get(
            "daily_plan",
            {}
        )

        sp_min = daily.get(
            "speaking",
            25
        )

        target = goal_data.get(
            "target_level",
            "B2"
        )

        days = goal_data.get(
            "days",
            60
        )

        self.ai_msg_lbl.setText(
            f"Maqsad: {target} — "
            f"{days} kun ichida!\n\n"
            f"Speaking eng zaif skill.\n"
            f"Bugun {sp_min} min "
            f"Speaking mashq qiling. 💪"
        )

    def _update_weekly(self, schedule):
        while self.weekly_content_l.count():
            item = (
                self.weekly_content_l.takeAt(0)
            )

            if item.widget():
                item.widget().deleteLater()

        today = datetime.now().strftime(
            "%A"
        )

        day_map = {
            "Monday": "Dushanba",
            "Tuesday": "Seshanba",
            "Wednesday": "Chorshanba",
            "Thursday": "Payshanba",
            "Friday": "Juma",
            "Saturday": "Shanba",
            "Sunday": "Yakshanba"
        }

        today_uz = day_map.get(
            today,
            ""
        )

        focus_colors = {
            "speaking": "#3B82F6",
            "writing": "#C084FC",
            "listening": "#8B5CF6",
            "reading": "#10B981",
            "vocabulary": "#4ADE80"
        }

        for day, info in schedule.items():
            focus = info.get(
                "focus",
                ""
            )

            total = info.get(
                "total",
                0
            )

            is_today = (
                day == today_uz
            )

            row = QHBoxLayout()

            color = focus_colors.get(
                focus,
                "#94A3B8"
            )

            marker = QLabel(
                "◉" if is_today
                else day[:2]
            )

            marker.setFixedWidth(24)
            marker.setStyleSheet(
                f"color:{'#F59E0B' if is_today else '#334155'};"
                f"font-size:{'12px' if is_today else '10px'};"
                "border:none;"
            )

            focus_lbl = QLabel(
                focus.title()
            )
            focus_lbl.setStyleSheet(
                f"color:{color};"
                "font-size:11px;"
                "border:none;"
            )

            time_lbl = QLabel(
                f"{total} min"
            )
            time_lbl.setStyleSheet(
                f"color:{'#F59E0B' if is_today else '#334155'};"
                "font-size:11px;"
                "border:none;"
            )

            row.addWidget(marker)
            row.addWidget(focus_lbl)
            row.addStretch()
            row.addWidget(time_lbl)

            self.weekly_content_l.addLayout(
                row
            )

        self.weekly_frame.show()

    def _start_session(self):
        print("▶ Session boshlandi!")

    def refresh(self):
        self._load_data()

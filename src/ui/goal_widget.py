import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QComboBox, QSlider,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from config.settings import CURRENT_SCORES, CEFR_LEVELS


class GoalSignals(QObject):
    plan_ready = pyqtSignal(dict)
    error = pyqtSignal(str)


class GoalWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.signals = GoalSignals()
        self.current_plan = None
        self.signals.plan_ready.connect(self._show_plan)
        self.signals.error.connect(self._show_error)
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{border:none;background:#0A0F1E;}"
        )

        content = QWidget()
        content.setStyleSheet("background:#0A0F1E;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header
        title = QLabel("🎯  Maqsad va Reja")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        sub = QLabel(
            "Maqsadingizni belgilang — AI o'quv rejangizni tuzadi"
        )
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Hozirgi holat
        current_frame = QFrame()
        current_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        cur_l = QVBoxLayout(current_frame)
        cur_l.setContentsMargins(20, 16, 20, 16)
        cur_l.setSpacing(12)

        cur_title = QLabel("HOZIRGI HOLAT")
        cur_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        cur_l.addWidget(cur_title)

        scores_row = QGridLayout()
        scores_row.setSpacing(10)

        skill_data = [
            ("🎧 Listening", CURRENT_SCORES["listening"],
             "#8B5CF6"),
            ("📖 Reading",   CURRENT_SCORES["reading"],
             "#10B981"),
            ("🎤 Speaking",  CURRENT_SCORES["speaking"],
             "#3B82F6"),
            ("✍️ Writing",   CURRENT_SCORES["writing"],
             "#C084FC"),
        ]

        for i, (skill, score, color) in enumerate(skill_data):
            sf = QFrame()
            sf.setStyleSheet(f"""
                QFrame {{
                    background:#0F172A;
                    border-radius:8px;
                    border:1px solid #1E293B;
                }}
            """)
            sl = QVBoxLayout(sf)
            sl.setContentsMargins(12, 10, 12, 10)
            sl.setSpacing(4)

            sk_l = QLabel(skill)
            sk_l.setStyleSheet(
                f"color:{color};font-size:11px;border:none;"
            )
            sc_l = QLabel(f"{score}/75")
            sc_l.setStyleSheet(
                "color:#F1F5F9;font-size:16px;"
                "font-weight:bold;border:none;"
            )
            pct = int(score / 75 * 100)
            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(4)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background:#1E293B;
                    border-radius:2px;border:none;
                }}
                QProgressBar::chunk {{
                    background:{color};border-radius:2px;
                }}
            """)
            sl.addWidget(sk_l)
            sl.addWidget(sc_l)
            sl.addWidget(bar)
            scores_row.addWidget(sf, i // 2, i % 2)

        cur_l.addLayout(scores_row)

        # Overall
        overall = CURRENT_SCORES["overall"]
        ov_row = QHBoxLayout()
        ov_lbl = QLabel(f"Overall: {overall}/75")
        ov_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:14px;"
            "font-weight:bold;"
        )
        level_lbl = QLabel("Daraja: B1")
        level_lbl.setStyleSheet(
            "background:#1E3A5F;color:#3B82F6;"
            "border-radius:6px;padding:3px 10px;"
            "font-size:12px;font-weight:bold;border:none;"
        )
        ov_row.addWidget(ov_lbl)
        ov_row.addStretch()
        ov_row.addWidget(level_lbl)
        cur_l.addLayout(ov_row)
        layout.addWidget(current_frame)

        # Maqsad sozlash
        goal_frame = QFrame()
        goal_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        goal_l = QVBoxLayout(goal_frame)
        goal_l.setContentsMargins(20, 16, 20, 16)
        goal_l.setSpacing(14)

        goal_title = QLabel("MAQSAD SOZLASH")
        goal_title.setStyleSheet(
            "color:#10B981;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        goal_l.addWidget(goal_title)

        # Maqsad daraja
        t_row = QHBoxLayout()
        t_lbl = QLabel("Maqsad daraja:")
        t_lbl.setStyleSheet(
            "color:#94A3B8;font-size:13px;"
        )
        t_lbl.setFixedWidth(150)
        self.target_combo = QComboBox()
        self.target_combo.addItems(["B2", "C1"])
        self.target_combo.setFixedHeight(36)
        self.target_combo.setStyleSheet("""
            QComboBox {
                background:#0F172A;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:8px;padding:6px 12px;
                font-size:13px;font-weight:bold;
            }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#131C31;color:#F1F5F9;
                border:1px solid #1E293B;
                selection-background-color:#1E3A5F;
            }
        """)
        t_row.addWidget(t_lbl)
        t_row.addWidget(self.target_combo)
        t_row.addStretch()
        goal_l.addLayout(t_row)

        # Vaqt
        d_row = QHBoxLayout()
        d_lbl = QLabel("Vaqt:")
        d_lbl.setStyleSheet(
            "color:#94A3B8;font-size:13px;"
        )
        d_lbl.setFixedWidth(150)
        self.days_combo = QComboBox()
        self.days_combo.addItems([
            "30 kun (1 oy)",
            "60 kun (2 oy)",
            "90 kun (3 oy)",
            "120 kun (4 oy)",
            "180 kun (6 oy)"
        ])
        self.days_combo.setCurrentIndex(1)
        self.days_combo.setFixedHeight(36)
        self.days_combo.setStyleSheet(
            self.target_combo.styleSheet()
        )
        d_row.addWidget(d_lbl)
        d_row.addWidget(self.days_combo)
        d_row.addStretch()
        goal_l.addLayout(d_row)

        # Kunlik vaqt
        m_row = QHBoxLayout()
        m_lbl = QLabel("Kunlik vaqt:")
        m_lbl.setStyleSheet(
            "color:#94A3B8;font-size:13px;"
        )
        m_lbl.setFixedWidth(150)

        self.minutes_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.minutes_slider.setRange(30, 180)
        self.minutes_slider.setValue(90)
        self.minutes_slider.setTickInterval(30)
        self.minutes_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background:#1E293B;
                height:6px;border-radius:3px;
            }
            QSlider::handle:horizontal {
                background:#3B82F6;
                width:16px;height:16px;
                margin:-5px 0;border-radius:8px;
            }
            QSlider::sub-page:horizontal {
                background:#3B82F6;border-radius:3px;
            }
        """)

        self.minutes_lbl = QLabel("90 min")
        self.minutes_lbl.setStyleSheet(
            "color:#3B82F6;font-size:13px;"
            "font-weight:bold;min-width:60px;"
        )
        self.minutes_slider.valueChanged.connect(
            lambda v: self.minutes_lbl.setText(f"{v} min")
        )

        m_row.addWidget(m_lbl)
        m_row.addWidget(self.minutes_slider, 1)
        m_row.addWidget(self.minutes_lbl)
        goal_l.addLayout(m_row)

        # Reja yaratish tugmasi
        create_btn = QPushButton("🎯  Reja Yaratish")
        create_btn.setFixedHeight(44)
        create_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        create_btn.setStyleSheet("""
            QPushButton {
                background:#10B981;color:white;
                border:none;border-radius:10px;
                font-size:14px;font-weight:bold;
            }
            QPushButton:hover { background:#059669; }
        """)
        create_btn.clicked.connect(self._create_plan)
        goal_l.addWidget(create_btn)
        layout.addWidget(goal_frame)

        # Reja ko'rsatish joyi
        self.plan_frame = QFrame()
        self.plan_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        self.plan_frame.hide()
        self.plan_l = QVBoxLayout(self.plan_frame)
        self.plan_l.setContentsMargins(20, 16, 20, 16)
        self.plan_l.setSpacing(12)
        layout.addWidget(self.plan_frame)

        layout.addStretch()
        scroll.setWidget(content)
        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.addWidget(scroll)

        # Mavjud rejani yuklash
        self._load_existing_plan()

    # ── REJA YARATISH ───────────────────────────────────────

    def _create_plan(self):
        target = self.target_combo.currentText()
        days_text = self.days_combo.currentText()
        days = int(days_text.split()[0])
        minutes = self.minutes_slider.value()

        def run():
            try:
                from src.smart_planner import SmartPlanner
                planner = SmartPlanner(self.db, self.ai)
                plan = planner.calculate_goal_plan(
                    target_level=target,
                    days=days,
                    daily_minutes=minutes
                )
                planner.save_goal(plan)
                planner.update_daily_tasks(plan)
                self.signals.plan_ready.emit(plan)
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _show_plan(self, plan):
        self.current_plan = plan

        # Eski widgetlarni o'chirish
        while self.plan_l.count():
            item = self.plan_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if plan.get("achieved"):
            msg = QLabel(plan.get("message", ""))
            msg.setStyleSheet(
                "color:#10B981;font-size:14px;"
            )
            self.plan_l.addWidget(msg)
            self.plan_frame.show()
            return

        # Plan header
        plan_title = QLabel("📋 SIZNING REJANIZ")
        plan_title.setStyleSheet(
            "color:#10B981;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.plan_l.addWidget(plan_title)

        # Asosiy info
        info_grid = QGridLayout()
        info_grid.setSpacing(10)

        info_items = [
            ("🎯 Maqsad", f"{plan['target_level']} ({plan['target_overall']}/75)", "#10B981"),
            ("📅 Muddat", f"{plan['days']} kun", "#3B82F6"),
            ("⏱️ Kun/vaqt", f"{plan['daily_minutes']} min", "#F59E0B"),
            ("📈 Kun/o'sish", f"+{plan['daily_gain_needed']} ball", "#8B5CF6"),
            ("🏁 Tugash", plan['end_date'], "#C084FC"),
            ("📊 Gap", f"+{plan['gap']} ball", "#EF4444"),
        ]

        for i, (lbl, val, color) in enumerate(info_items):
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background:#0F172A;
                    border-radius:8px;
                    border:1px solid #1E293B;
                }}
            """)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(12, 8, 12, 8)
            fl.setSpacing(2)
            ll = QLabel(lbl)
            ll.setStyleSheet(
                "color:#475569;font-size:10px;border:none;"
            )
            vl = QLabel(val)
            vl.setStyleSheet(
                f"color:{color};font-size:13px;"
                "font-weight:bold;border:none;"
            )
            fl.addWidget(ll)
            fl.addWidget(vl)
            info_grid.addWidget(f, i // 3, i % 3)

        self.plan_l.addLayout(info_grid)

        # Kunlik taqsimot
        dist_title = QLabel("KUNLIK VAQT TAQSIMOTI")
        dist_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.plan_l.addWidget(dist_title)

        daily = plan.get("daily_plan", {})
        colors = {
            "speaking":   "#3B82F6",
            "writing":    "#C084FC",
            "listening":  "#8B5CF6",
            "reading":    "#10B981",
            "vocabulary": "#4ADE80"
        }
        icons = {
            "speaking":   "🎤",
            "writing":    "✍️",
            "listening":  "🎧",
            "reading":    "📖",
            "vocabulary": "📚"
        }

        for skill, minutes in sorted(
            daily.items(),
            key=lambda x: x[1], reverse=True
        ):
            color = colors.get(skill, "#3B82F6")
            icon = icons.get(skill, "📄")
            total_min = plan.get("daily_minutes", 90)
            pct = int(minutes / total_min * 100)

            row = QHBoxLayout()
            sk_lbl = QLabel(f"{icon} {skill.title()}")
            sk_lbl.setStyleSheet(
                f"color:{color};font-size:13px;"
                "font-weight:bold;border:none;"
            )
            sk_lbl.setFixedWidth(110)

            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background:#1E293B;
                    border-radius:4px;border:none;
                }}
                QProgressBar::chunk {{
                    background:{color};border-radius:4px;
                }}
            """)

            min_lbl = QLabel(f"{minutes} min")
            min_lbl.setStyleSheet(
                f"color:{color};font-size:12px;"
                "font-weight:bold;border:none;min-width:55px;"
            )
            min_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

            row.addWidget(sk_lbl)
            row.addWidget(bar, 1)
            row.addWidget(min_lbl)
            self.plan_l.addLayout(row)

        # Milestones
        mile_title = QLabel("MILESTONE SANALAR")
        mile_title.setStyleSheet(
            "color:#F59E0B;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.plan_l.addWidget(mile_title)

        milestones = plan.get("milestones", [])
        mile_row = QHBoxLayout()
        mile_row.setSpacing(8)

        for m in milestones:
            mf = QFrame()
            reached = m.get("reached", False)
            mf.setStyleSheet(f"""
                QFrame {{
                    background:{'#0F2A1E' if reached else '#0F172A'};
                    border-radius:8px;
                    border:1px solid {'#10B981' if reached else '#1E293B'};
                }}
            """)
            ml = QVBoxLayout(mf)
            ml.setContentsMargins(10, 8, 10, 8)
            ml.setSpacing(2)

            pct_l = QLabel(m["label"])
            pct_l.setStyleSheet(
                f"color:{'#10B981' if reached else '#F59E0B'};"
                "font-size:12px;font-weight:bold;border:none;"
            )
            pct_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

            score_l = QLabel(f"{m['score']}/75")
            score_l.setStyleSheet(
                "color:#F1F5F9;font-size:11px;border:none;"
            )
            score_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

            date_l = QLabel(m["date"])
            date_l.setStyleSheet(
                "color:#475569;font-size:10px;border:none;"
            )
            date_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ml.addWidget(pct_l)
            ml.addWidget(score_l)
            ml.addWidget(date_l)
            mile_row.addWidget(mf)

        self.plan_l.addLayout(mile_row)

        # Taxminiy natija
        proj = plan.get("projected_scores", {})
        if proj:
            proj_title = QLabel("TAXMINIY NATIJA")
            proj_title.setStyleSheet(
                "color:#8B5CF6;font-size:11px;"
                "font-weight:bold;letter-spacing:1px;"
            )
            self.plan_l.addWidget(proj_title)

            proj_row = QHBoxLayout()
            proj_row.setSpacing(8)

            for skill, score in proj.items():
                if skill == "overall":
                    continue
                color = colors.get(skill, "#3B82F6")
                pf = QFrame()
                pf.setStyleSheet("""
                    QFrame {
                        background:#0F172A;
                        border-radius:8px;
                        border:1px solid #1E293B;
                    }
                """)
                pl = QVBoxLayout(pf)
                pl.setContentsMargins(8, 6, 8, 6)
                pl.setSpacing(2)

                sk_l = QLabel(skill.title())
                sk_l.setStyleSheet(
                    f"color:{color};font-size:10px;border:none;"
                )
                sk_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

                sc_l = QLabel(f"{score}")
                sc_l.setStyleSheet(
                    f"color:{color};font-size:14px;"
                    "font-weight:bold;border:none;"
                )
                sc_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

                pl.addWidget(sk_l)
                pl.addWidget(sc_l)
                proj_row.addWidget(pf)

            # Overall
            ov_score = proj.get("overall", 0)
            ov_f = QFrame()
            ov_f.setStyleSheet("""
                QFrame {
                    background:#0F2A1E;
                    border-radius:8px;
                    border:1px solid #10B981;
                }
            """)
            ov_fl = QVBoxLayout(ov_f)
            ov_fl.setContentsMargins(8, 6, 8, 6)
            ov_fl.setSpacing(2)
            ov_tl = QLabel("Overall")
            ov_tl.setStyleSheet(
                "color:#10B981;font-size:10px;border:none;"
            )
            ov_tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ov_sl = QLabel(f"{ov_score}")
            ov_sl.setStyleSheet(
                "color:#10B981;font-size:14px;"
                "font-weight:bold;border:none;"
            )
            ov_sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ov_fl.addWidget(ov_tl)
            ov_fl.addWidget(ov_sl)
            proj_row.addWidget(ov_f)

            self.plan_l.addLayout(proj_row)

        self.plan_frame.show()

    def _show_error(self, error):
        err = QLabel(f"❌ {error[:80]}")
        err.setStyleSheet(
            "color:#EF4444;font-size:12px;"
        )
        self.plan_l.addWidget(err)
        self.plan_frame.show()

    def _load_existing_plan(self):
        def run():
            try:
                from src.smart_planner import SmartPlanner
                planner = SmartPlanner(self.db, self.ai)
                plan = planner.load_goal()
                if plan:
                    self.signals.plan_ready.emit(plan)
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    def refresh(self):
        pass
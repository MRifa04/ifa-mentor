import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from config.settings import CEFR_LEVELS
class ExamCard(QFrame):
    def __init__(self, title, duration,
                 questions, level, color,
                 icon, on_start):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
                border-top:3px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size:24px;border:none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color:#F1F5F9;font-size:15px;"
            f"font-weight:bold;border:none;"
        )
        level_lbl = QLabel(level)
        level_lbl.setStyleSheet(
            f"background:{color};"
            f"color:#FFFFFF;"
            f"border:none;"
            f"border-radius:6px;padding:3px 10px;"
            f"font-size:11px;font-weight:bold;"
        )
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(level_lbl)
        layout.addLayout(header)

        # Info
        info = QHBoxLayout()
        info.setSpacing(16)

        for label, value in [
            ("⏱️", f"{duration} min"),
            ("❓", f"{questions} savol"),
        ]:
            item = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:14px;border:none;")
            val = QLabel(value)
            val.setStyleSheet(
                "color:#94A3B8;font-size:12px;border:none;"
            )
            item.addWidget(lbl)
            item.addWidget(val)
            info.addLayout(item)

        info.addStretch()
        layout.addLayout(info)

        # Start button
        start_btn = QPushButton(f"▶  Boshlash")
        start_btn.setFixedHeight(38)
        start_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background:{color};color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }}
            QPushButton:hover {{ opacity:0.9; }}
        """)
        start_btn.clicked.connect(on_start)
        layout.addWidget(start_btn)


class MockExamsWidget(QWidget):
    def __init__(self, db, ai, on_start_mock=None):
        super().__init__()
        self.db = db
        self.ai = ai
        self.on_start_mock = on_start_mock
        self.is_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.elapsed = 0
        self._build()
    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

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
        title = QLabel("🎓  Mock Imtihonlar")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        sub = QLabel(
            "Haqiqiy imtihon formatida mashq qiling"
        )
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Status panel
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        self.status_frame.hide()
        status_l = QVBoxLayout(self.status_frame)
        status_l.setContentsMargins(20, 16, 20, 16)
        status_l.setSpacing(12)

        status_header = QHBoxLayout()
        self.status_title = QLabel("Imtihon ketmoqda...")
        self.status_title.setStyleSheet(
            "color:#F1F5F9;font-size:15px;"
            "font-weight:bold;"
        )
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setStyleSheet(
            "color:#3B82F6;font-size:18px;"
            "font-weight:bold;"
        )
        status_header.addWidget(self.status_title)
        status_header.addStretch()
        status_header.addWidget(self.timer_lbl)
        status_l.addLayout(status_header)

        self.current_skill_lbl = QLabel("")
        self.current_skill_lbl.setStyleSheet(
            "color:#94A3B8;font-size:13px;"
        )
        status_l.addWidget(self.current_skill_lbl)

        self.exam_progress = QProgressBar()
        self.exam_progress.setValue(0)
        self.exam_progress.setTextVisible(False)
        self.exam_progress.setFixedHeight(8)
        self.exam_progress.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:4px;border:none;
            }
            QProgressBar::chunk {
                background:#3B82F6;border-radius:4px;
            }
        """)
        status_l.addWidget(self.exam_progress)

        stop_btn = QPushButton("⏹  To'xtatish")
        stop_btn.setFixedHeight(36)
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.setStyleSheet("""
            QPushButton {
                background:#2D1B1B;color:#EF4444;
                border:1px solid #EF4444;
                border-radius:8px;font-size:12px;
            }
            QPushButton:hover { background:#3D2020; }
        """)
        stop_btn.clicked.connect(self._stop_exam)
        status_l.addWidget(stop_btn)
        layout.addWidget(self.status_frame)

        # Alohida imtihonlar
        section_title = QLabel("ALOHIDA IMTIHONLAR")
        section_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        layout.addWidget(section_title)

        exams = [
            {
                "title": "Listening Mock",
                "duration": 40,
                "questions": 30,
                "level": "B1-C1",
                "color": "#8B5CF6",
                "icon": "🎧",
                "key": "listening"
            },
            {
                "title": "Reading Mock",
                "duration": 60,
                "questions": 35,
                "level": "B1-C1",
                "color": "#10B981",
                "icon": "📖",
                "key": "reading"
            },
            {
                "title": "Writing Mock",
                "duration": 70,
                "questions": 2,
                "level": "B2-C1",
                "color": "#C084FC",
                "icon": "✍️",
                "key": "writing"
            },
            {
                "title": "Speaking Mock",
                "duration": 30,
                "questions": 8,
                "level": "B1-C1",
                "color": "#3B82F6",
                "icon": "🎤",
                "key": "speaking"
            },
        ]

        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(12)

        for i, exam in enumerate(exams):
            card = ExamCard(
                title=exam["title"],
                duration=exam["duration"],
                questions=exam["questions"],
                level=exam["level"],
                color=exam["color"],
                icon=exam["icon"],
                on_start=lambda chk, k=exam["key"]:
                    self._start_single(k)
            )
            grid_layout.addWidget(card)
            if i == 1:
                layout.addLayout(grid_layout)
                grid_layout = QHBoxLayout()
                grid_layout.setSpacing(12)

        if grid_layout.count() > 0:
            layout.addLayout(grid_layout)

        # To'liq mock imtihon
        full_section = QLabel("TO'LIQ MOCK IMTIHON")
        full_section.setStyleSheet(
            "color:#F59E0B;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        layout.addWidget(full_section)

        full_frame = QFrame()
        full_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #F59E0B44;
                border-top:3px solid #F59E0B;
            }
        """)
        full_l = QVBoxLayout(full_frame)
        full_l.setContentsMargins(20, 18, 20, 18)
        full_l.setSpacing(12)

        full_header = QHBoxLayout()
        full_icon = QLabel("🏆")
        full_icon.setStyleSheet("font-size:28px;border:none;")
        full_title_l = QVBoxLayout()
        full_title = QLabel("To'liq CEFR Mock Imtihon")
        full_title.setStyleSheet(
            "color:#F1F5F9;font-size:16px;"
            "font-weight:bold;border:none;"
        )
        full_sub = QLabel(
            "Listening + Reading + Writing + Speaking"
        )
        full_sub.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        full_title_l.addWidget(full_title)
        full_title_l.addWidget(full_sub)

        full_header.addWidget(full_icon)
        full_header.addLayout(full_title_l)
        full_header.addStretch()
        full_l.addLayout(full_header)

        # Info
        info_row = QHBoxLayout()
        info_row.setSpacing(20)
        for label, val in [
            ("⏱️", "~3.5 soat"),
            ("❓", "73+ savol"),
            ("📊", "B1 → C1"),
        ]:
            il = QHBoxLayout()
            ll = QLabel(label)
            ll.setStyleSheet("font-size:14px;border:none;")
            vl = QLabel(val)
            vl.setStyleSheet(
                "color:#94A3B8;font-size:12px;border:none;"
            )
            il.addWidget(ll)
            il.addWidget(vl)
            info_row.addLayout(il)
        info_row.addStretch()
        full_l.addLayout(info_row)

        full_btn = QPushButton(
            "🏆  To'liq Mock Imtihonni Boshlash"
        )
        full_btn.setFixedHeight(44)
        full_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        full_btn.setStyleSheet("""
            QPushButton {
                background:#F59E0B;color:white;
                border:none;border-radius:8px;
                font-size:14px;font-weight:bold;
            }
            QPushButton:hover { background:#D97706; }
        """)
        full_btn.clicked.connect(self._start_full)
        full_l.addWidget(full_btn)
        layout.addWidget(full_frame)

        # Oxirgi natijalar
        history_title = QLabel("OXIRGI NATIJALAR")
        history_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        layout.addWidget(history_title)

        self.history_frame = QFrame()
        self.history_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        self.history_l = QVBoxLayout(self.history_frame)
        self.history_l.setContentsMargins(16, 14, 16, 14)
        self.history_l.setSpacing(8)
        layout.addWidget(self.history_frame)
        layout.addStretch()

        scroll.setWidget(content)
        main.addWidget(scroll)

        self._load_history()

    def _load_history(self):
        while self.history_l.count():
            item = self.history_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT skill, score, max_score,
                   percentage, date, duration_minutes
            FROM sessions
            ORDER BY created_at DESC
            LIMIT 8
        """)
        rows = cursor.fetchall()
        self.db.close()

        if not rows:
            no_hist = QLabel(
                "Hali hech qanday imtihon topshirilmagan"
            )
            no_hist.setStyleSheet(
                "color:#475569;font-size:13px;border:none;"
            )
            no_hist.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_l.addWidget(no_hist)
            return

        skill_colors = {
            "Reading":    "#10B981",
            "Listening":  "#8B5CF6",
            "Speaking":   "#3B82F6",
            "Writing":    "#C084FC",
        }
        skill_icons = {
            "Reading":    "📖",
            "Listening":  "🎧",
            "Speaking":   "🎤",
            "Writing":    "✍️",
        }

        for row in rows:
            skill = row["skill"]
            score = row["score"]
            max_s = row["max_score"]
            pct = row["percentage"] or 0
            date = row["date"] or ""

            color = skill_colors.get(skill, "#3B82F6")
            icon = skill_icons.get(skill, "📄")

            item = QFrame()
            item.setStyleSheet(f"""
                QFrame {{
                    background:#0F172A;
                    border-radius:8px;
                    border-left:3px solid {color};
                }}
            """)
            item_l = QHBoxLayout(item)
            item_l.setContentsMargins(12, 8, 12, 8)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                "font-size:16px;border:none;"
            )
            icon_lbl.setFixedWidth(24)

            skill_lbl = QLabel(skill)
            skill_lbl.setStyleSheet(
                f"color:{color};font-size:12px;"
                "font-weight:bold;border:none;"
            )
            skill_lbl.setFixedWidth(80)

            score_lbl = QLabel(f"{score}/{max_s}")
            score_lbl.setStyleSheet(
                "color:#F1F5F9;font-size:12px;border:none;"
            )

            pct_lbl = QLabel(f"{int(pct)}%")
            result_color = (
                "#10B981" if pct >= 60 else "#F59E0B"
            )
            pct_lbl.setStyleSheet(
                f"color:{result_color};font-size:12px;"
                "font-weight:bold;border:none;"
            )

            date_lbl = QLabel(date)
            date_lbl.setStyleSheet(
                "color:#475569;font-size:11px;border:none;"
            )

            item_l.addWidget(icon_lbl)
            item_l.addWidget(skill_lbl)
            item_l.addWidget(score_lbl)
            item_l.addStretch()
            item_l.addWidget(pct_lbl)
            item_l.addWidget(date_lbl)
            self.history_l.addWidget(item)

    # ── IMTIHON BOSHQARUV ───────────────────────────────────

    def _start_single(self, skill):
        if self.is_running:
            return
        if not self.on_start_mock:
            return
        self.on_start_mock("single", skill)

    def _start_full(self):
        if self.is_running:
            return
        if not self.on_start_mock:
            return
        self.on_start_mock("full")

    def begin_session(self, title, skill=None, step=1, total=4):
        self.is_running = True
        self.elapsed = 0
        self.timer.start(1000)
        self.status_frame.show()
        if skill:
            self.status_title.setText(f"{skill} imtihoni ketmoqda...")
            self.current_skill_lbl.setText(
                f"🔄 {skill} ({step}/{total}) — {title}"
            )
        else:
            self.status_title.setText("To'liq Mock Imtihon ketmoqda...")
            self.current_skill_lbl.setText(title)
        pct = int(((step - 1) / total) * 100) if total else 0
        self.exam_progress.setValue(max(pct, 5))

    def on_skill_complete(self, skill, score, max_score, step, total):
        self.current_skill_lbl.setText(
            f"✅ {skill}: {score}/{max_score} ({step}/{total})"
        )
        pct = int((step / total) * 100) if total else 100
        self.exam_progress.setValue(pct)

    def show_results(self, results, title="Mock Imtihon"):
        self.is_running = False
        self.timer.stop()
        self.status_title.setText("✅ Imtihon tugadi!")
        lines = []
        for skill, data in results.items():
            score = data.get("score", 0)
            max_score = data.get("max_score", 75)
            lines.append(f"{skill}: {score}/{max_score}")
        self.current_skill_lbl.setText(
            " | ".join(lines) if lines else title
        )
        self.exam_progress.setValue(100)
        self._load_history()

    def _stop_exam(self):
        self.is_running = False
        self.timer.stop()
        self.status_frame.hide()
        self.exam_progress.setValue(0)
        if self.on_start_mock:
            parent = self.window()
            if parent and hasattr(parent, "stop_mock_exam"):
                parent.stop_mock_exam()

    def _tick(self):
        self.elapsed += 1
        m = self.elapsed // 60
        s = self.elapsed % 60
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

    def refresh(self):
        self._load_history()
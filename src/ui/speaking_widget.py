import os
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from src.ui.styles import SKILL_COLORS
from src.ui.daily_task import DailyTaskMixin

class WorkerSignals(QObject):
    question_ready = pyqtSignal(dict)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    analyzing = pyqtSignal()
    result_ready = pyqtSignal(dict)
    session_complete = pyqtSignal(dict)
    error = pyqtSignal(str)

class QuestionCard(QFrame):
    def __init__(self, question, part, total):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Part badge
        badge = QLabel(f"Part {part[-1]} — Speaking")
        badge.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )
        layout.addWidget(badge)

        # Savol
        q_lbl = QLabel(question)
        q_lbl.setStyleSheet(
            "color: #F1F5F9; font-size: 16px;"
            "font-weight: bold; line-height: 1.5;"
        )
        q_lbl.setWordWrap(True)
        layout.addWidget(q_lbl)

        # Hint
        hint = QLabel(
            "💡 1-2 daqiqa gapiring. "
            "Aniq va ravon gapiring."
        )
        hint.setStyleSheet("color: #475569; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)


class ScoreRow(QFrame):
    def __init__(self, label, score, color):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        lbl = QLabel(label)
        lbl.setFixedWidth(120)
        lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")

        bar = QProgressBar()
        bar.setValue(int(score))
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: #1E293B;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)

        score_lbl = QLabel(f"{int(score)}")
        score_lbl.setFixedWidth(35)
        score_lbl.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: bold;"
        )
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(lbl)
        layout.addWidget(bar)
        layout.addWidget(score_lbl)


class SpeakingWidget(QWidget, DailyTaskMixin):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.init_daily_task()
        self.signals = WorkerSignals()
        self.current_part = "Part1"
        self.is_recording = False
        self.timer_seconds = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._connect_signals()
        self._build()

    def _connect_signals(self):
        self.signals.question_ready.connect(self._show_question)
        self.signals.recording_started.connect(self._on_rec_start)
        self.signals.recording_stopped.connect(self._on_rec_stop)
        self.signals.analyzing.connect(self._on_analyzing)
        self.signals.result_ready.connect(self._show_result)
        self.signals.session_complete.connect(self._show_complete)
        self.signals.error.connect(self._show_error)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.attach_task_banner(outer)

        content = QWidget()
        main = QHBoxLayout(content)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── CHAP: Asosiy kontent ──
        left = QWidget()
        left.setStyleSheet("background: #0A0F1E;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(28, 24, 20, 24)
        left_layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("🎤  Speaking Practice")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #F1F5F9;"
        )
        header.addWidget(title)
        header.addStretch()
        left_layout.addLayout(header)

        sub = QLabel(
            "Mikrofon orqali gapiring — AI sizni baholaydi"
        )
        sub.setStyleSheet("color: #94A3B8; font-size: 13px;")
        left_layout.addWidget(sub)

        # Part tanlash
        part_frame = QFrame()
        part_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 10px;
                border: 1px solid #1E293B;
            }
        """)
        part_layout = QHBoxLayout(part_frame)
        part_layout.setContentsMargins(16, 12, 16, 12)
        part_layout.setSpacing(8)

        part_lbl = QLabel("Part tanlang:")
        part_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        part_layout.addWidget(part_lbl)

        self.part_btns = {}
        parts = [
            ("Part 1", "Part1", "Shaxsiy savollar"),
            ("Part 2", "Part2", "Rasm tavsifi"),
            ("Part 3", "Part3", "Argumentli nutq"),
        ]
        for label, key, desc in parts:
            btn = QPushButton(f"{label}\n{desc}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._part_btn_style(False))
            btn.clicked.connect(
                lambda chk, k=key, b=btn: self._select_part(k, b)
            )
            self.part_btns[key] = btn
            part_layout.addWidget(btn)

        part_layout.addStretch()
        left_layout.addWidget(part_frame)

        # Savol kartasi
        self.question_area = QFrame()
        self.question_area.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
                min-height: 140px;
            }
        """)
        q_layout = QVBoxLayout(self.question_area)
        q_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_lbl = QLabel(
            "▶  Boshlash tugmasini bosing"
        )
        self.question_lbl.setStyleSheet(
            "color: #475569; font-size: 15px;"
        )
        self.question_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_lbl.setWordWrap(True)
        q_layout.addWidget(self.question_lbl)
        left_layout.addWidget(self.question_area)

        # Yozish paneli
        rec_frame = QFrame()
        rec_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        rec_layout = QVBoxLayout(rec_frame)
        rec_layout.setContentsMargins(24, 20, 24, 20)
        rec_layout.setSpacing(16)

        # Timer
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setStyleSheet(
            "font-size: 42px; font-weight: bold;"
            "color: #3B82F6; letter-spacing: 4px;"
        )
        self.timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rec_layout.addWidget(self.timer_lbl)

        # Waveform (simulatsiya)
        self.wave_lbl = QLabel("━ ━ ━ ━ ━ ━ ━ ━ ━ ━")
        self.wave_lbl.setStyleSheet(
            "color: #1E293B; font-size: 18px; letter-spacing: 4px;"
        )
        self.wave_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rec_layout.addWidget(self.wave_lbl)

        # Status
        self.status_lbl = QLabel("Boshlashga tayyor")
        self.status_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 13px;"
        )
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rec_layout.addWidget(self.status_lbl)

        # Tugmalar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.start_btn = QPushButton("▶  Boshlash")
        self.start_btn.setFixedHeight(44)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2563EB; }
        """)
        self.start_btn.clicked.connect(self._start_session)

        self.stop_btn = QPushButton("⏹  To'xtatish")
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #DC2626; }
            QPushButton:disabled {
                background: #1E293B;
                color: #475569;
            }
        """)
        self.stop_btn.clicked.connect(self._stop_recording)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        rec_layout.addLayout(btn_layout)
        left_layout.addWidget(rec_frame)
        left_layout.addStretch()

        # ── O'NG: Natijalar ──
        right = QWidget()
        right.setFixedWidth(320)
        right.setStyleSheet(
            "background: #0F172A;"
            "border-left: 1px solid #1E293B;"
        )
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 24, 20, 24)
        right_layout.setSpacing(16)

        result_title = QLabel("AI Baholash")
        result_title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #F1F5F9;"
        )
        right_layout.addWidget(result_title)

        # Overall score
        self.overall_frame = QFrame()
        self.overall_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        overall_layout = QVBoxLayout(self.overall_frame)
        overall_layout.setContentsMargins(16, 16, 16, 16)

        self.overall_lbl = QLabel("—")
        self.overall_lbl.setStyleSheet(
            "font-size: 42px; font-weight: bold; color: #3B82F6;"
        )
        self.overall_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cefr_lbl = QLabel("Hali baholanmagan")
        self.cefr_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 13px;"
        )
        self.cefr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        overall_layout.addWidget(self.overall_lbl)
        overall_layout.addWidget(self.cefr_lbl)
        right_layout.addWidget(self.overall_frame)

        # Score bars
        scores_frame = QFrame()
        scores_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        self.scores_layout = QVBoxLayout(scores_frame)
        self.scores_layout.setContentsMargins(16, 14, 16, 14)
        self.scores_layout.setSpacing(8)

        scores_title = QLabel("Batafsil natija")
        scores_title.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )
        self.scores_layout.addWidget(scores_title)

        for label, color in [
            ("Fluency",       "#10B981"),
            ("Grammar",       "#3B82F6"),
            ("Vocabulary",    "#8B5CF6"),
            ("Pronunciation", "#F59E0B"),
        ]:
            row = ScoreRow(label, 0, color)
            self.scores_layout.addWidget(row)

        right_layout.addWidget(scores_frame)

        # AI Feedback
        feedback_frame = QFrame()
        feedback_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        fb_layout = QVBoxLayout(feedback_frame)
        fb_layout.setContentsMargins(16, 14, 16, 14)

        fb_title = QLabel("AI Feedback")
        fb_title.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )

        self.feedback_lbl = QLabel(
            "Gapiring — AI sizni tinglaydi va baholaydi..."
        )
        self.feedback_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 12px; line-height: 1.5;"
        )
        self.feedback_lbl.setWordWrap(True)

        fb_layout.addWidget(fb_title)
        fb_layout.addWidget(self.feedback_lbl)
        right_layout.addWidget(feedback_frame)
        right_layout.addStretch()

        # Tavsiyalar
        tips_btn = QPushButton("💡 Tavsiyalarni ko'rish")
        tips_btn.setFixedHeight(38)
        tips_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tips_btn.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #334155;
                color: #F1F5F9;
            }
        """)
        tips_btn.clicked.connect(self._show_tips)
        right_layout.addWidget(tips_btn)

        main.addWidget(left, 1)
        main.addWidget(right)

        outer.addWidget(content, 1)

        # Default Part1
        self._select_part("Part1", self.part_btns["Part1"])

    # ── PART TANLASH ────────────────────────────────────────

    def _part_btn_style(self, active):
        if active:
            return """
                QPushButton {
                    background: #1E3A5F;
                    color: #3B82F6;
                    border: 1px solid #3B82F6;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """
        return """
            QPushButton {
                background: #0F172A;
                color: #94A3B8;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #1E293B;
                color: #F1F5F9;
            }
        """

    def _select_part(self, part, btn):
        for k, b in self.part_btns.items():
            b.setStyleSheet(self._part_btn_style(False))
        btn.setStyleSheet(self._part_btn_style(True))
        self.current_part = part
        self.question_lbl.setText(
            f"▶  {part} uchun boshlash tugmasini bosing"
        )

    # ── SESSIYA ─────────────────────────────────────────────

    def _start_session(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.is_recording = True
        self.timer_seconds = 0
        self.timer.start(1000)

        self._update_wave(True)
        self.status_lbl.setText("🔴 Yozilmoqda...")
        self.status_lbl.setStyleSheet(
            "color: #EF4444; font-size: 13px;"
        )

        # Background thread
        thread = threading.Thread(
            target=self._run_session,
            daemon=True
        )
        thread.start()

    def _run_session(self):
        try:
            from src.speaking import SpeakingModule
            speaking = SpeakingModule(self.db, self.ai)
            speaking.run_practice_session(
                part_name=self.current_part,
                callback=self._session_callback
            )
        except Exception as e:
            self.signals.error.emit(str(e))

    def _session_callback(self, event, data):
        if event == "question":
            self.signals.question_ready.emit(data)
        elif event == "recording_start":
            self.signals.recording_started.emit()
        elif event == "recording_stop":
            self.signals.recording_stopped.emit()
        elif event == "analyzing":
            self.signals.analyzing.emit()
        elif event == "result":
            self.signals.result_ready.emit(data)
        elif event == "session_complete":
            self.signals.session_complete.emit(data)

    def _stop_recording(self):
        self.is_recording = False
        self.timer.stop()
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.status_lbl.setText("⏹ To'xtatildi")
        self.status_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 13px;"
        )
        self._update_wave(False)

    # ── TIMER ───────────────────────────────────────────────

    def _tick(self):
        self.timer_seconds += 1
        m = self.timer_seconds // 60
        s = self.timer_seconds % 60
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")
        self._animate_wave()

    def _animate_wave(self):
        waves = [
            "▁ ▃ ▅ ▇ ▅ ▃ ▁ ▃ ▅ ▇",
            "▃ ▅ ▇ ▅ ▃ ▁ ▃ ▅ ▇ ▅",
            "▅ ▇ ▅ ▃ ▁ ▃ ▅ ▇ ▅ ▃",
            "▇ ▅ ▃ ▁ ▃ ▅ ▇ ▅ ▃ ▁",
        ]
        idx = self.timer_seconds % len(waves)
        self.wave_lbl.setText(waves[idx])

    def _update_wave(self, active):
        if active:
            self.wave_lbl.setStyleSheet(
                "color: #3B82F6; font-size: 18px; letter-spacing: 4px;"
            )
        else:
            self.wave_lbl.setStyleSheet(
                "color: #1E293B; font-size: 18px; letter-spacing: 4px;"
            )
            self.wave_lbl.setText("━ ━ ━ ━ ━ ━ ━ ━ ━ ━")

    # ── SIGNAL HANDLERLARI ──────────────────────────────────

    def _show_question(self, data):
        q = data.get("question", "")
        self.question_lbl.setText(q)
        self.question_lbl.setStyleSheet(
            "color: #F1F5F9; font-size: 15px; font-weight: bold;"
        )
        self.question_area.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #3B82F6;
                min-height: 140px;
            }
        """)

    def _on_rec_start(self):
        self.status_lbl.setText("🔴 Gapiring...")
        self._update_wave(True)

    def _on_rec_stop(self):
        self.status_lbl.setText("⏸ Tahlil qilinmoqda...")
        self._update_wave(False)

    def _on_analyzing(self):
        self.status_lbl.setText("🤖 AI baholayapti...")
        self.feedback_lbl.setText("AI sizning javobingizni tahlil qilmoqda...")
        self.feedback_lbl.setStyleSheet(
            "color: #3B82F6; font-size: 12px;"
        )

    def _show_result(self, data):
        scores = data.get("scores", {})
        overall = data.get("overall", 0)
        cefr = data.get("cefr_level", "B1")
        feedback = data.get("feedback", "")
        improvements = data.get("improvements", [])

        # Overall
        self.overall_lbl.setText(str(int(overall)))
        self.overall_lbl.setStyleSheet(
            f"font-size: 42px; font-weight: bold;"
            f"color: {'#10B981' if overall >= 60 else '#F59E0B'};"
        )
        self.cefr_lbl.setText(f"CEFR daraja: {cefr}")

        # Score bars yangilash
        colors = {
            "Fluency": "#10B981",
            "Grammar": "#3B82F6",
            "Vocabulary": "#8B5CF6",
            "Pronunciation": "#F59E0B"
        }
        # Eski barlarni o'chirish
        while self.scores_layout.count() > 1:
            item = self.scores_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for criterion, color in colors.items():
            score_data = scores.get(criterion, {})
            score = score_data.get("score", 0)
            row = ScoreRow(criterion, score, color)
            self.scores_layout.addWidget(row)

        # Feedback
        imp_text = "\n".join(
            [f"• {i}" for i in improvements[:3]]
        )
        self.feedback_lbl.setText(
            f"{feedback}\n\n{imp_text}" if imp_text else feedback
        )
        self.feedback_lbl.setStyleSheet(
            "color: #CBD5E1; font-size: 12px; line-height: 1.5;"
        )

        # Timer to'xtatish
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_lbl.setText("✅ Baholash tugadi")
        self.status_lbl.setStyleSheet(
            "color: #10B981; font-size: 13px;"
        )

    def _show_complete(self, data):
        avg = data.get("average_score", 0)
        self.question_lbl.setText(
            f"✅ Sessiya tugadi!\n"
            f"O'rtacha ball: {avg}/100"
        )
        self.question_lbl.setStyleSheet(
            "color: #10B981; font-size: 15px; font-weight: bold;"
        )
        self.finish_skill_task(int(avg), 100)

    def _show_error(self, error):
        self.status_lbl.setText(f"❌ Xato: {error}")
        self.status_lbl.setStyleSheet(
            "color: #EF4444; font-size: 12px;"
        )
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.timer.stop()

    def _show_tips(self):
        from src.speaking import SpeakingModule
        speaking = SpeakingModule(self.db, self.ai)
        tips = speaking.get_improvement_tips()
        self.feedback_lbl.setText(tips)
        self.feedback_lbl.setStyleSheet(
            "color: #F59E0B; font-size: 12px; line-height: 1.5;"
        )

    def apply_mock_exam_task(self, task):
        DailyTaskMixin.apply_mock_exam_task(self, task)
        if not task:
            return
        pdf = task.get("pdf_material")
        if pdf:
            self._start_mock_speaking(pdf)
        else:
            self._select_part("Part3", self.part_btns["Part3"])

    def _start_mock_speaking(self, material):
        from src.mock_pdf_text import get_speaking_from_pdf

        prompt = get_speaking_from_pdf(material.get("file_path", ""))
        if prompt.strip():
            self.feedback_lbl.setText(prompt[:1200])
            self.feedback_lbl.setStyleSheet(
                "color:#CBD5E1;font-size:12px;line-height:1.5;"
            )
        self._select_part("Part3", self.part_btns["Part3"])

    def apply_daily_task(self, task):
        super().apply_daily_task(task)
        if not task:
            return
        if task.get("task_type") == "mock":
            self._select_part("Part3", self.part_btns["Part3"])
        else:
            self._select_part("Part1", self.part_btns["Part1"])

    def refresh(self):
        if self.mock_exam_task and self._task_banner_label:
            task = self.mock_exam_task
            title = task.get("mock_title", "Mock")
            skill = task.get("skill", "")
            step = task.get("step", 1)
            total = task.get("total_steps", 4)
            self._task_banner_label.setText(
                f"🎓 Mock: {title} — {skill} ({step}/{total})"
            )
            self._task_banner.show()
        elif self.daily_task and self._task_banner_label:
            self.apply_daily_task(self.daily_task)
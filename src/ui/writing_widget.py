import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QTextEdit, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from config.settings import USER_NAME

from src.ui.daily_task import DailyTaskMixin

class WritingSignals(QObject):
    task_ready = pyqtSignal(dict)
    evaluating = pyqtSignal()
    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

class WritingWidget(QWidget, DailyTaskMixin):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.init_daily_task()
        self.signals = WritingSignals()
        self.current_task = None
        self.timer_seconds = 0
        self.timer_limit = 30 * 60
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._connect_signals()
        self._build()

    def _connect_signals(self):
        self.signals.task_ready.connect(self._show_task)
        self.signals.evaluating.connect(self._on_evaluating)
        self.signals.result_ready.connect(self._show_result)
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

        # ── CHAP ──
        left = QWidget()
        left.setStyleSheet("background:#0A0F1E;")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(28, 24, 20, 24)
        left_l.setSpacing(16)

        # Header
        title = QLabel("✍️  Writing Practice")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        left_l.addWidget(title)

        sub = QLabel(
            "Formal letter yoki argumentative essay yozing"
        )
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        left_l.addWidget(sub)

        # Task tanlash
        task_frame = QFrame()
        task_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        task_l = QHBoxLayout(task_frame)
        task_l.setContentsMargins(16, 12, 16, 12)
        task_l.setSpacing(10)

        task_lbl = QLabel("Vazifa:")
        task_lbl.setStyleSheet("color:#94A3B8;font-size:12px;")
        task_l.addWidget(task_lbl)

        self.task_btns = {}
        for key, label, desc in [
            ("formal_letter",
             "Formal Letter", "150+ so'z • 30 min"),
            ("argumentative_essay",
             "Essay", "250+ so'z • 40 min"),
        ]:
            btn = QPushButton(f"{label}\n{desc}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._task_style(
                key == "formal_letter"
            ))
            btn.clicked.connect(
                lambda chk, k=key, b=btn:
                self._select_task(k, b)
            )
            self.task_btns[key] = btn
            task_l.addWidget(btn)

        task_l.addStretch()
        left_l.addWidget(task_frame)

        # Topshiriq kartasi
        self.prompt_frame = QFrame()
        self.prompt_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
                min-height:80px;
            }
        """)
        prompt_l = QVBoxLayout(self.prompt_frame)
        prompt_l.setContentsMargins(18, 14, 18, 14)

        self.prompt_title = QLabel("TOPSHIRIQ")
        self.prompt_title.setStyleSheet(
            "color:#3B82F6;font-size:10px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.prompt_lbl = QLabel(
            "▶  Boshlash tugmasini bosing — AI topshiriq beradi"
        )
        self.prompt_lbl.setStyleSheet(
            "color:#475569;font-size:13px;"
        )
        self.prompt_lbl.setWordWrap(True)

        self.points_lbl = QLabel("")
        self.points_lbl.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )
        self.points_lbl.setWordWrap(True)

        prompt_l.addWidget(self.prompt_title)
        prompt_l.addWidget(self.prompt_lbl)
        prompt_l.addWidget(self.points_lbl)
        left_l.addWidget(self.prompt_frame)

        # Yozish maydoni
        editor_frame = QFrame()
        editor_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        editor_l = QVBoxLayout(editor_frame)
        editor_l.setContentsMargins(16, 14, 16, 14)
        editor_l.setSpacing(8)

        # Editor header
        ed_header = QHBoxLayout()
        ed_title = QLabel("Javobingiz")
        ed_title.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )
        self.word_count_lbl = QLabel("0 so'z")
        self.word_count_lbl.setStyleSheet(
            "color:#3B82F6;font-size:12px;font-weight:bold;"
        )
        ed_header.addWidget(ed_title)
        ed_header.addStretch()
        ed_header.addWidget(self.word_count_lbl)
        editor_l.addLayout(ed_header)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Bu yerga yozing...\n\n"
            "Maslahat: Avval outline (reja) tuzing,\n"
            "keyin paragraflarni yozing."
        )
        self.editor.setStyleSheet("""
            QTextEdit {
                background:#0F172A;
                color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:8px;
                padding:12px;
                font-size:13px;
                line-height:1.6;
            }
            QTextEdit:focus {
                border:1px solid #3B82F6;
            }
        """)
        self.editor.setMinimumHeight(200)
        self.editor.textChanged.connect(self._count_words)
        editor_l.addWidget(self.editor)
        left_l.addWidget(editor_frame)

        # Tugmalar
        btn_l = QHBoxLayout()
        btn_l.setSpacing(10)

        self.get_task_btn = QPushButton("📋  Topshiriq olish")
        self.get_task_btn.setFixedHeight(42)
        self.get_task_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.get_task_btn.setStyleSheet("""
            QPushButton {
                background:#1E293B;
                color:#94A3B8;
                border:1px solid #334155;
                border-radius:8px;
                font-size:13px;
            }
            QPushButton:hover {
                background:#334155;color:#F1F5F9;
            }
        """)
        self.get_task_btn.clicked.connect(self._get_task)

        self.submit_btn = QPushButton("✅  Topshirish va Baholash")
        self.submit_btn.setFixedHeight(42)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;
                color:white;
                border:none;
                border-radius:8px;
                font-size:13px;
                font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
            QPushButton:disabled {
                background:#1E293B;color:#475569;
            }
        """)
        self.submit_btn.clicked.connect(self._submit)

        self.clear_btn = QPushButton("🗑️  Tozalash")
        self.clear_btn.setFixedHeight(42)
        self.clear_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background:#1E293B;
                color:#EF4444;
                border:1px solid #334155;
                border-radius:8px;
                font-size:13px;
            }
            QPushButton:hover { background:#334155; }
        """)
        self.clear_btn.clicked.connect(
            lambda: self.editor.clear()
        )

        btn_l.addWidget(self.get_task_btn)
        btn_l.addWidget(self.submit_btn, 1)
        btn_l.addWidget(self.clear_btn)
        left_l.addLayout(btn_l)

        # ── O'NG ──
        right = QWidget()
        right.setFixedWidth(320)
        right.setStyleSheet(
            "background:#0F172A;"
            "border-left:1px solid #1E293B;"
        )
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(20, 24, 20, 24)
        right_l.setSpacing(14)

        # Timer
        timer_frame = QFrame()
        timer_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        timer_l = QVBoxLayout(timer_frame)
        timer_l.setContentsMargins(16, 14, 16, 14)
        timer_l.setSpacing(8)

        timer_title = QLabel("VAQT")
        timer_title.setStyleSheet(
            "color:#3B82F6;font-size:10px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.timer_lbl = QLabel("30:00")
        self.timer_lbl.setStyleSheet(
            "font-size:36px;font-weight:bold;color:#F1F5F9;"
        )
        self.timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_bar = QProgressBar()
        self.timer_bar.setValue(100)
        self.timer_bar.setTextVisible(False)
        self.timer_bar.setFixedHeight(4)
        self.timer_bar.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:2px;border:none;
            }
            QProgressBar::chunk {
                background:#3B82F6;border-radius:2px;
            }
        """)

        self.timer_btn = QPushButton("▶  Boshlash")
        self.timer_btn.setFixedHeight(34)
        self.timer_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.timer_btn.setStyleSheet("""
            QPushButton {
                background:#1E3A5F;color:#3B82F6;
                border:1px solid #3B82F6;
                border-radius:6px;font-size:12px;
            }
            QPushButton:hover { background:#1E293B; }
        """)
        self.timer_btn.clicked.connect(self._toggle_timer)

        timer_l.addWidget(timer_title)
        timer_l.addWidget(self.timer_lbl)
        timer_l.addWidget(self.timer_bar)
        timer_l.addWidget(self.timer_btn)
        right_l.addWidget(timer_frame)

        # AI Baholash
        score_title = QLabel("AI Baholash")
        score_title.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#F1F5F9;"
        )
        right_l.addWidget(score_title)

        scores_frame = QFrame()
        scores_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        self.scores_l = QVBoxLayout(scores_frame)
        self.scores_l.setContentsMargins(16, 14, 16, 14)
        self.scores_l.setSpacing(10)

        overall_lbl = QLabel("Umumiy ball")
        overall_lbl.setStyleSheet(
            "color:#3B82F6;font-size:10px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.scores_l.addWidget(overall_lbl)

        self.overall_lbl = QLabel("—  / 5.0")
        self.overall_lbl.setStyleSheet(
            "font-size:28px;font-weight:bold;color:#F1F5F9;"
        )
        self.scores_l.addWidget(self.overall_lbl)

        self.cefr_badge = QLabel("Hali baholanmagan")
        self.cefr_badge.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )
        self.scores_l.addWidget(self.cefr_badge)

        criteria = [
            ("Task Achievement",  "#10B981"),
            ("Coherence",         "#3B82F6"),
            ("Lexical Resource",  "#8B5CF6"),
            ("Grammar Range",     "#F59E0B"),
        ]
        self.criterion_bars = {}
        for crit, color in criteria:
            row = QHBoxLayout()
            lbl = QLabel(crit)
            lbl.setStyleSheet(
                "color:#94A3B8;font-size:11px;"
            )
            lbl.setFixedWidth(130)
            bar = QProgressBar()
            bar.setValue(0)
            bar.setMaximum(5)
            bar.setTextVisible(False)
            bar.setFixedHeight(5)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background:#1E293B;
                    border-radius:2px;border:none;
                }}
                QProgressBar::chunk {{
                    background:{color};border-radius:2px;
                }}
            """)
            score_l = QLabel("0.0")
            score_l.setFixedWidth(28)
            score_l.setStyleSheet(
                f"color:{color};font-size:11px;"
                "font-weight:bold;"
            )
            row.addWidget(lbl)
            row.addWidget(bar)
            row.addWidget(score_l)
            self.scores_l.addLayout(row)
            self.criterion_bars[crit] = (bar, score_l)

        right_l.addWidget(scores_frame)

        # Feedback
        fb_frame = QFrame()
        fb_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        fb_l = QVBoxLayout(fb_frame)
        fb_l.setContentsMargins(16, 14, 16, 14)

        fb_title = QLabel("AI Feedback")
        fb_title.setStyleSheet(
            "color:#3B82F6;font-size:10px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.feedback_lbl = QLabel(
            "Yozing va topshiring —\n"
            "AI sizning esseyingizni baholaydi."
        )
        self.feedback_lbl.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )
        self.feedback_lbl.setWordWrap(True)

        fb_l.addWidget(fb_title)
        fb_l.addWidget(self.feedback_lbl)
        right_l.addWidget(fb_frame)
        right_l.addStretch()

        main.addWidget(left, 1)
        main.addWidget(right)
        outer.addWidget(content, 1)

        self.current_task_type = "formal_letter"

    # ── TASK TANLASH ────────────────────────────────────────

    def _task_style(self, active):
        if active:
            return """
                QPushButton {
                    background:#1E3A5F;color:#3B82F6;
                    border:1px solid #3B82F6;
                    border-radius:8px;padding:8px 14px;
                    font-size:11px;font-weight:bold;
                }
            """
        return """
            QPushButton {
                background:#0F172A;color:#94A3B8;
                border:1px solid #1E293B;
                border-radius:8px;padding:8px 14px;
                font-size:11px;
            }
            QPushButton:hover {
                background:#1E293B;color:#F1F5F9;
            }
        """

    def _select_task(self, key, btn):
        for b in self.task_btns.values():
            b.setStyleSheet(self._task_style(False))
        btn.setStyleSheet(self._task_style(True))
        self.current_task_type = key
        limit = 30 if key == "formal_letter" else 40
        self.timer_limit = limit * 60
        self.timer_seconds = 0
        m = limit
        self.timer_lbl.setText(f"{m:02d}:00")
        self.timer_bar.setValue(100)

    # ── TOPSHIRIQ OLISH ─────────────────────────────────────

    def _get_task(self):
        self.get_task_btn.setEnabled(False)
        self.prompt_lbl.setText("⏳ AI topshiriq tayyorlamoqda...")
        self.prompt_lbl.setStyleSheet(
            "color:#3B82F6;font-size:13px;"
        )

        def run():
            from src.writing import WritingModule
            wm = WritingModule(self.db, self.ai)
            task = wm.get_task(self.current_task_type)
            self.signals.task_ready.emit(task)

        threading.Thread(target=run, daemon=True).start()

    def _show_task(self, task):
        self.current_task = task
        instructions = task.get("instructions", "")
        points = task.get("points_to_cover", [])

        self.prompt_lbl.setText(instructions)
        self.prompt_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:13px;"
        )
        self.prompt_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #3B82F6;
                min-height:80px;
            }
        """)

        if points:
            pts = "  •  ".join(points)
            self.points_lbl.setText(f"📌 {pts}")

        self.get_task_btn.setEnabled(True)
        self.editor.setFocus()

    # ── TOPSHIRISH ──────────────────────────────────────────

    def _submit(self):
        essay = self.editor.toPlainText().strip()
        if not essay:
            self.feedback_lbl.setText(
                "❌ Avval biror narsa yozing!"
            )
            return

        words = len(essay.split())
        min_words = 150 if (
            self.current_task_type == "formal_letter"
        ) else 250

        if words < min_words:
            self.feedback_lbl.setText(
                f"⚠️  Kamida {min_words} so'z yozing!\n"
                f"Hozir: {words} so'z"
            )
            self.feedback_lbl.setStyleSheet(
                "color:#F59E0B;font-size:12px;"
            )
            return

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("🔄  Baholanmoqda...")
        self.signals.evaluating.emit()

        prompt_text = self.current_task.get(
            "instructions", ""
        ) if self.current_task else ""

        def run():
            try:
                result = self.ai.evaluate_writing(
                    task_type=self.current_task_type,
                    prompt_text=prompt_text,
                    user_essay=essay
                )
                self.signals.result_ready.emit(result)
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_evaluating(self):
        self.feedback_lbl.setText(
            "🤖 AI esseyingizni tahlil qilmoqda..."
        )
        self.feedback_lbl.setStyleSheet(
            "color:#3B82F6;font-size:12px;"
        )

    def _show_result(self, result):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("✅  Topshirish va Baholash")

        if "error" in result:
            self.feedback_lbl.setText(
                f"❌ API xatosi — API kalitni tekshiring"
            )
            return

        overall = result.get("overall", 0)
        cefr = result.get("cefr_level", "B1")
        strengths = result.get("strengths", [])
        improvements = result.get("improvements", [])

        self.overall_lbl.setText(f"{overall}  / 5.0")
        color = "#10B981" if overall >= 3.5 else "#F59E0B"
        self.overall_lbl.setStyleSheet(
            f"font-size:28px;font-weight:bold;color:{color};"
        )
        self.cefr_badge.setText(f"CEFR daraja: {cefr}")
        self.cefr_badge.setStyleSheet(
            f"color:{color};font-size:12px;font-weight:bold;"
        )

        # Criterion bars
        scores = result.get("scores", {})
        mapping = {
            "Task Achievement":  "Task Achievement",
            "Coherence":         "Coherence_Cohesion",
            "Lexical Resource":  "Lexical_Resource",
            "Grammar Range":     "Grammar_Range",
        }
        for crit, key in mapping.items():
            if crit in self.criterion_bars:
                bar, lbl = self.criterion_bars[crit]
                score_data = scores.get(key, {})
                score = score_data.get("score", 0)
                bar.setValue(int(score))
                lbl.setText(str(score))

        # Feedback
        st = "\n".join([f"✅ {s}" for s in strengths[:2]])
        im = "\n".join([f"→ {i}" for i in improvements[:2]])
        self.feedback_lbl.setText(
            f"{st}\n\n{im}" if st or im
            else result.get("band_feedback", "")
        )
        self.feedback_lbl.setStyleSheet(
            "color:#CBD5E1;font-size:12px;"
        )

        # DB ga saqlash
        self.db.save_session(
            skill="Writing",
            score=int(overall * 20),
            max_score=100,
            duration=self.timer_seconds // 60,
            details=result
        )
        self.db.update_progress(
            "writing",
            int(float(overall) * 15),
        )
        self.finish_skill_task(
            int(float(overall) * 20),
            100,
        )
        self.timer.stop()

    def _show_error(self, error):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("✅  Topshirish va Baholash")
        self.feedback_lbl.setText(f"❌ Xato: {error}")

    # ── TIMER ───────────────────────────────────────────────

    def _toggle_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.timer_btn.setText("▶  Davom etish")
        else:
            self.timer.start(1000)
            self.timer_btn.setText("⏸  Pauza")

    def _tick(self):
        self.timer_seconds += 1
        remaining = self.timer_limit - self.timer_seconds
        if remaining <= 0:
            self.timer.stop()
            self.timer_lbl.setText("00:00")
            self.timer_lbl.setStyleSheet(
                "font-size:36px;font-weight:bold;color:#EF4444;"
            )
            self.timer_btn.setText("⏰  Vaqt tugadi!")
            return

        m = remaining // 60
        s = remaining % 60
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

        pct = int((remaining / self.timer_limit) * 100)
        self.timer_bar.setValue(pct)

        color = (
            "#EF4444" if pct < 25
            else "#F59E0B" if pct < 50
            else "#3B82F6"
        )
        self.timer_bar.setStyleSheet(f"""
            QProgressBar {{
                background:#1E293B;
                border-radius:2px;border:none;
            }}
            QProgressBar::chunk {{
                background:{color};border-radius:2px;
            }}
        """)

    # ── SO'Z HISOBLASH ──────────────────────────────────────

    def _count_words(self):
        text = self.editor.toPlainText().strip()
        words = len(text.split()) if text else 0
        min_w = 150 if (
            self.current_task_type == "formal_letter"
        ) else 250
        color = "#10B981" if words >= min_w else "#F59E0B"
        self.word_count_lbl.setText(f"{words} so'z")
        self.word_count_lbl.setStyleSheet(
            f"color:{color};font-size:12px;font-weight:bold;"
        )

    def apply_mock_exam_task(self, task):
        DailyTaskMixin.apply_mock_exam_task(self, task)
        if not task:
            return
        pdf = task.get("pdf_material")
        if pdf:
            self._start_mock_writing(pdf)

    def _start_mock_writing(self, material):
        from src.mock_pdf_text import get_writing_from_pdf

        self.start_btn.setEnabled(False)
        self.result_frame.hide()
        self.submit_btn.setEnabled(True)
        self.timer_seconds = 0
        self.timer_limit = 40 * 60
        self.timer.start(1000)

        prompt = get_writing_from_pdf(material.get("file_path", ""))
        if not prompt.strip():
            prompt = (
                "Mock imtihon Writing vazifasi.\n"
                "PDF dan vazifa topilmadi — erkin essay yozing."
            )

        task = {
            "instructions": prompt,
            "points_to_cover": [],
            "type": "mock_exam",
        }
        self.current_task_type = "argumentative_essay"
        self._show_task(task)

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
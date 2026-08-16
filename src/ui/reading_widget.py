import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QRadioButton,
    QButtonGroup, QTextEdit,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from src.ui.daily_task import DailyTaskMixin


class ReadingSignals(QObject):
    text_ready = pyqtSignal(str, str)
    questions_ready = pyqtSignal(dict)
    error = pyqtSignal(str)


class PartBadge(QLabel):
    def __init__(self, part, level):
        super().__init__(f"{part} • {level}")
        colors = {
            "B1": "#10B981",
            "B2": "#3B82F6",
            "C1": "#8B5CF6"
        }
        color = colors.get(level, "#94A3B8")
        self.setStyleSheet(
            f"background:{color};"
            f"color:#FFFFFF;"
            f"border:none;"
            f"border-radius:6px;padding:3px 10px;"
            f"font-size:11px;font-weight:bold;"
        )
        self.setFixedHeight(24)


class QuestionItem(QFrame):
    def __init__(self, q_data, q_num, q_type):
        super().__init__()
        self.q_data = q_data
        self.q_num = q_num
        self.q_type = q_type
        self.selected = None
        self.btn_group = QButtonGroup(self)
        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        q_text = (
            q_data.get("question", "")
            or q_data.get("statement", "")
            or q_data.get("sentence", "")
        )
        q_lbl = QLabel(f"{q_num}. {q_text}")
        q_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:13px;"
            "font-weight:bold;border:none;"
        )
        q_lbl.setWordWrap(True)
        layout.addWidget(q_lbl)

        options = q_data.get("options", {})
        if isinstance(options, dict) and options:
            for key, val in options.items():
                rb = QRadioButton(f"{key})  {val}")
                rb.setStyleSheet(self._rb_style())
                rb.toggled.connect(
                    lambda chk, k=key: self._select(k)
                )
                self.btn_group.addButton(rb)
                layout.addWidget(rb)
        elif q_type == "true_false":
            for opt in ["True", "False", "Not Given"]:
                rb = QRadioButton(opt)
                rb.setStyleSheet(self._rb_style())
                rb.toggled.connect(
                    lambda chk, o=opt: self._select(o)
                )
                self.btn_group.addButton(rb)
                layout.addWidget(rb)

    def _rb_style(self):
        return """
            QRadioButton {
                color:#CBD5E1;font-size:12px;
                border:none;padding:4px;
            }
            QRadioButton:hover { color:#F1F5F9; }
            QRadioButton::indicator {
                width:14px;height:14px;
            }
            QRadioButton::indicator:checked {
                background:#3B82F6;
                border-radius:7px;
                border:2px solid #3B82F6;
            }
            QRadioButton::indicator:unchecked {
                background:transparent;
                border-radius:7px;
                border:2px solid #475569;
            }
        """

    def _select(self, key):
        self.selected = key

    def get_answer(self):
        return self.selected or ""

    def show_result(self, correct_ans):
        is_correct = (
            str(self.selected or "").upper()
            == str(correct_ans).upper()
        )
        color = "#10B981" if is_correct else "#EF4444"
        self.setStyleSheet(f"""
            QFrame {{
                background:#131C31;
                border-radius:10px;
                border:1px solid {color};
            }}
        """)
        if not is_correct:
            ans_lbl = QLabel(f"✓ To'g'ri: {correct_ans}")
            ans_lbl.setStyleSheet(
                f"color:{color};font-size:11px;border:none;"
            )
            self.layout().addWidget(ans_lbl)
        return is_correct


class ReadingWidget(QWidget, DailyTaskMixin):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.init_daily_task()
        self.signals = ReadingSignals()
        self.current_text = ""
        self.current_part = "Part3"
        self.question_items = []
        self.timer_seconds = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._connect_signals()
        self._build()

    def _connect_signals(self):
        self.signals.text_ready.connect(self._show_text)
        self.signals.questions_ready.connect(
            self._show_questions
        )
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

        # ── CHAP: Matn ──
        left = QWidget()
        left.setStyleSheet("background:#0A0F1E;")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(24, 20, 12, 20)
        left_l.setSpacing(12)

        title = QLabel("📖  Reading Practice")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#F1F5F9;"
        )
        left_l.addWidget(title)

        # Part tanlash
        part_frame = QFrame()
        part_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        part_l = QHBoxLayout(part_frame)
        part_l.setContentsMargins(12, 10, 12, 10)
        part_l.setSpacing(6)

        part_lbl = QLabel("Part:")
        part_lbl.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )
        part_l.addWidget(part_lbl)

        self.part_btns = {}
        for part, level in [
            ("Part1","B1"),("Part2","B1"),
            ("Part3","B2"),("Part4","B2"),
            ("Part5","C1"),("Part6","C1"),
        ]:
            btn = QPushButton(f"{part[-1]}")
            btn.setFixedSize(32, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                self._part_btn_style(part == "Part3")
            )
            btn.clicked.connect(
                lambda chk, p=part: self._select_part(p)
            )
            self.part_btns[part] = btn
            part_l.addWidget(btn)

        part_l.addStretch()
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setStyleSheet(
            "color:#3B82F6;font-size:13px;font-weight:bold;"
        )
        part_l.addWidget(self.timer_lbl)
        left_l.addWidget(part_frame)

        # Matn
        text_frame = QFrame()
        text_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        text_l = QVBoxLayout(text_frame)
        text_l.setContentsMargins(16, 14, 16, 14)

        text_header = QHBoxLayout()
        self.text_title = QLabel("MATN")
        self.text_title.setStyleSheet(
            "color:#3B82F6;font-size:10px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        text_header.addWidget(self.text_title)
        text_header.addStretch()
        text_l.addLayout(text_header)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText(
            "Matn bu yerda ko'rsatiladi...\n\n"
            "▶ Boshlash tugmasini bosing"
        )
        self.text_area.setStyleSheet("""
            QTextEdit {
                background:#0F172A;color:#CBD5E1;
                border:none;border-radius:6px;
                padding:12px;font-size:13px;
            }
        """)
        self.text_area.setMinimumHeight(300)
        text_l.addWidget(self.text_area)
        left_l.addWidget(text_frame, 1)

        self.start_btn = QPushButton("▶  Boshlash")
        self.start_btn.setFixedHeight(42)
        self.start_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.start_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
        """)
        self.start_btn.clicked.connect(self._start)
        left_l.addWidget(self.start_btn)

        # ── O'NG: Savollar ──
        right = QWidget()
        right.setFixedWidth(380)
        right.setStyleSheet(
            "background:#0F172A;"
            "border-left:1px solid #1E293B;"
        )
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(16, 20, 16, 20)
        right_l.setSpacing(12)

        q_header = QHBoxLayout()
        q_title = QLabel("SAVOLLAR")
        q_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        self.q_count_lbl = QLabel("")
        self.q_count_lbl.setStyleSheet(
            "color:#475569;font-size:11px;"
        )
        q_header.addWidget(q_title)
        q_header.addStretch()
        q_header.addWidget(self.q_count_lbl)
        right_l.addLayout(q_header)

        self.q_progress = QProgressBar()
        self.q_progress.setValue(0)
        self.q_progress.setTextVisible(False)
        self.q_progress.setFixedHeight(4)
        self.q_progress.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:2px;border:none;
            }
            QProgressBar::chunk {
                background:#3B82F6;border-radius:2px;
            }
        """)
        right_l.addWidget(self.q_progress)

        q_scroll = QScrollArea()
        q_scroll.setWidgetResizable(True)
        q_scroll.setStyleSheet(
            "QScrollArea{border:none;background:transparent;}"
        )

        self.q_container = QWidget()
        self.q_container.setStyleSheet("background:transparent;")
        self.q_layout = QVBoxLayout(self.q_container)
        self.q_layout.setContentsMargins(0, 0, 0, 0)
        self.q_layout.setSpacing(10)

        self.q_placeholder = QLabel(
            "Matn yuklanganidan keyin\nsavollar bu yerda chiqadi"
        )
        self.q_placeholder.setStyleSheet(
            "color:#475569;font-size:13px;border:none;"
        )
        self.q_placeholder.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.q_layout.addWidget(self.q_placeholder)
        self.q_layout.addStretch()

        q_scroll.setWidget(self.q_container)
        right_l.addWidget(q_scroll, 1)

        # Natija
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        self.result_frame.hide()
        res_l = QVBoxLayout(self.result_frame)
        res_l.setContentsMargins(14, 12, 14, 12)
        res_l.setSpacing(6)

        self.res_score = QLabel("—")
        self.res_score.setStyleSheet(
            "font-size:28px;font-weight:bold;color:#3B82F6;"
        )
        self.res_score.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.res_cefr = QLabel("")
        self.res_cefr.setStyleSheet(
            "font-size:13px;color:#94A3B8;"
        )
        self.res_cefr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        res_l.addWidget(self.res_score)
        res_l.addWidget(self.res_cefr)
        right_l.addWidget(self.result_frame)

        self.submit_btn = QPushButton("✅  Tekshirish")
        self.submit_btn.setFixedHeight(42)
        self.submit_btn.setEnabled(False)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background:#10B981;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#059669; }
            QPushButton:disabled {
                background:#1E293B;color:#475569;
            }
        """)
        self.submit_btn.clicked.connect(self._submit)
        right_l.addWidget(self.submit_btn)

        main.addWidget(left, 1)
        main.addWidget(right)
        outer.addWidget(content, 1)

    def _part_btn_style(self, active):
        if active:
            return (
                'QPushButton{'
                'background:#1E3A5F;color:#3B82F6;'
                'border:1px solid #3B82F6;'
                'border-radius:6px;font-size:11px;'
                'font-weight:bold;}'
            )
        return (
            'QPushButton{'
            'background:#0F172A;color:#94A3B8;'
            'border:1px solid #1E293B;'
            'border-radius:6px;font-size:11px;}'
            'QPushButton:hover{'
            'background:#1E293B;color:#F1F5F9;}'
        )

    def _select_part(self, part):
        for p, b in self.part_btns.items():
            b.setStyleSheet(self._part_btn_style(p == part))
        self.current_part = part

    def _start(self):
        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳ Yuklanmoqda...")
        self.result_frame.hide()
        self.submit_btn.setEnabled(False)
        self.timer_seconds = 0
        self.timer.start(1000)

        def run():
            try:
                from src.reading import ReadingModule
                from config.settings import READING_RULES
                rm = ReadingModule(self.db, self.ai)

                material = self.db.get_unused_material(
                    "reading", "pdf"
                )
                if material:
                    text = rm.get_text_from_material(material)
                    title = material.get("title", "Material")
                else:
                    text = rm._generate_sample_text()
                    title = "AI Generated Text"

                self.signals.text_ready.emit(text, title)

                rule = READING_RULES["parts"].get(
                    self.current_part, {}
                )
                level = rule.get("level", "B2")
                count = rule.get("questions", 5)
                q_type = rule.get("type", "multiple_choice")

                questions = self.ai.generate_reading_questions(
                    text=text,
                    part_name=self.current_part,
                    level=level,
                    question_type=q_type,
                    count=count
                )
                questions["part"] = self.current_part
                questions["level"] = level
                questions["q_type"] = q_type
                self.signals.questions_ready.emit(questions)

            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _show_text(self, text, title):
        self.current_text = text
        self.text_title.setText(f"MATN — {title[:40]}")
        self.text_area.setPlainText(text)

    def _show_questions(self, data):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🔄  Yangi matn")

        questions = data.get("questions", [])
        q_type = data.get("q_type", "multiple_choice")
        part = data.get("part", "Part3")
        level = data.get("level", "B2")

        while self.q_layout.count():
            item = self.q_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.question_items = []

        if not questions:
            err = QLabel("❌ Savollar generatsiya xatosi")
            err.setStyleSheet(
                "color:#EF4444;font-size:12px;border:none;"
            )
            self.q_layout.addWidget(err)
            return

        badge = PartBadge(part, level)
        self.q_layout.addWidget(badge)

        for i, q in enumerate(questions):
            item = QuestionItem(q, i + 1, q_type)
            self.q_layout.addWidget(item)
            self.question_items.append((item, q))

        self.q_layout.addStretch()

        total = len(questions)
        self.q_count_lbl.setText(f"0/{total} javoblandi")
        self.q_progress.setValue(0)
        self.submit_btn.setEnabled(True)

    def _submit(self):
        self.submit_btn.setEnabled(False)
        self.timer.stop()

        correct = 0
        total = len(self.question_items)

        for item, q_data in self.question_items:
            correct_ans = q_data.get("answer", "")
            is_correct = item.show_result(correct_ans)
            if is_correct:
                correct += 1

        pct = int(correct / total * 100) if total else 0

        from config.settings import READING_RULES
        rule = READING_RULES["parts"].get(
            self.current_part, {}
        )
        level = rule.get("level", "B2")

        if pct >= 60:
            cefr_msg = f"✅ {level} — O'tdingiz!"
            color = "#10B981"
        else:
            cefr_msg = f"⚠️ {level} — Yana mashq kerak"
            color = "#F59E0B"

        self.res_score.setText(f"{correct}/{total} ({pct}%)")
        self.res_score.setStyleSheet(
            f"font-size:28px;font-weight:bold;color:{color};"
        )
        self.res_cefr.setText(cefr_msg)
        self.result_frame.show()

        self.db.save_session(
            skill="Reading",
            score=correct,
            max_score=total,
            duration=self.timer_seconds // 60,
            details={
                "part": self.current_part,
                "correct": correct,
                "total": total
            }
        )
        self.db.update_study_dna(
            "Reading",
            rule.get("type", "multiple_choice"),
            correct=correct,
            total=total
        )
        self.db.update_progress("reading", int(pct * 0.75))
        self.finish_skill_task(correct, total)
        self.q_count_lbl.setText(
            f"{total}/{total} javoblandi"
        )
        self.q_progress.setValue(100)

    def _show_error(self, error):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶  Boshlash")
        self.timer.stop()
        while self.q_layout.count():
            item = self.q_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        err = QLabel(f"❌ {error[:80]}")
        err.setStyleSheet(
            "color:#EF4444;font-size:12px;border:none;"
        )
        err.setWordWrap(True)
        self.q_layout.addWidget(err)
        self.q_layout.addStretch()

    def _tick(self):
        self.timer_seconds += 1
        m = self.timer_seconds // 60
        s = self.timer_seconds % 60
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

    def apply_mock_exam_task(self, task):
        DailyTaskMixin.apply_mock_exam_task(self, task)
        if not task:
            return
        pdf = task.get("pdf_material")
        if pdf:
            self._start_mock_reading(pdf)

    def _start_mock_reading(self, material):
        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳ Yuklanmoqda...")
        self.result_frame.hide()
        self.submit_btn.setEnabled(False)
        self.timer_seconds = 0
        self.timer.start(1000)

        def run():
            try:
                from src.mock_pdf_text import get_reading_part_from_pdf
                from src.reading import ReadingModule
                from config.settings import READING_RULES

                rm = ReadingModule(self.db, self.ai)
                pdf_path = material.get("file_path", "")
                part_num = int(self.current_part.replace("Part", ""))
                part_text = get_reading_part_from_pdf(pdf_path, part_num)
                if part_text.strip():
                    text = part_text
                else:
                    text = rm.get_text_from_material(material)

                title = material.get("set_title") or material.get(
                    "title", "Mock PDF"
                )
                self.signals.text_ready.emit(text, title)

                rule = READING_RULES["parts"].get(
                    self.current_part, {}
                )
                level = rule.get("level", "B2")
                count = rule.get("questions", 5)
                q_type = rule.get("type", "multiple_choice")

                questions = self.ai.generate_reading_questions(
                    text=text,
                    part_name=self.current_part,
                    level=level,
                    question_type=q_type,
                    count=count,
                )
                questions["part"] = self.current_part
                questions["level"] = level
                questions["q_type"] = q_type
                self.signals.questions_ready.emit(questions)
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

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
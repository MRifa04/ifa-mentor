import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit,
    QStackedWidget, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from src.ui.daily_task import DailyTaskMixin


class VocabSignals(QObject):
    word_added = pyqtSignal(dict)
    review_loaded = pyqtSignal(list)
    error = pyqtSignal(str)


class FlashCard(QFrame):
    def __init__(self, word_data, on_know, on_dont):
        super().__init__()
        self.word_data = word_data
        self.flipped = False
        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:16px;
                border:1px solid #1E293B;
            }
        """)
        self.setMinimumHeight(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        layout.setSpacing(10)

        self.word_lbl = QLabel(word_data.get("word", ""))
        self.word_lbl.setStyleSheet(
            "font-size:34px;font-weight:bold;"
            "color:#F1F5F9;border:none;"
        )
        self.word_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.word_lbl)

        pron = word_data.get("pronunciation", "")
        if pron:
            pron_lbl = QLabel(pron)
            pron_lbl.setStyleSheet(
                "font-size:13px;color:#94A3B8;border:none;"
            )
            pron_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(pron_lbl)

        self.hidden = QFrame()
        self.hidden.setStyleSheet("background:transparent;border:none;")
        hl = QVBoxLayout(self.hidden)
        hl.setSpacing(6)

        uzbek = QLabel(f"🇺🇿  {word_data.get('uzbek', '')}")
        uzbek.setStyleSheet(
            "font-size:17px;font-weight:bold;"
            "color:#10B981;border:none;"
        )
        uzbek.setAlignment(Qt.AlignmentFlag.AlignCenter)

        defn = QLabel(word_data.get("definition", ""))
        defn.setStyleSheet("font-size:12px;color:#CBD5E1;border:none;")
        defn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        defn.setWordWrap(True)

        ex = QLabel(f'"{word_data.get("example_ai", "")}"')
        ex.setStyleSheet(
            "font-size:11px;color:#64748B;"
            "font-style:italic;border:none;"
        )
        ex.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ex.setWordWrap(True)

        hl.addWidget(uzbek)
        hl.addWidget(defn)
        hl.addWidget(ex)
        self.hidden.hide()
        layout.addWidget(self.hidden)

        self.hint = QLabel("👆 Bosing — tarjimani ko'ring")
        self.hint.setStyleSheet(
            "font-size:11px;color:#475569;border:none;"
        )
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint)
        layout.addStretch()

        btn_l = QHBoxLayout()
        dont_btn = QPushButton("✗  Bilmadim")
        dont_btn.setFixedHeight(42)
        dont_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dont_btn.setStyleSheet("""
            QPushButton {
                background:#2D1B1B;color:#EF4444;
                border:1px solid #EF4444;
                border-radius:8px;font-size:13px;
                font-weight:bold;
            }
            QPushButton:hover { background:#3D2020; }
        """)
        dont_btn.clicked.connect(on_dont)

        know_btn = QPushButton("✓  Bildim")
        know_btn.setFixedHeight(42)
        know_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        know_btn.setStyleSheet("""
            QPushButton {
                background:#10B981;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#059669; }
        """)
        know_btn.clicked.connect(on_know)

        btn_l.addWidget(dont_btn)
        btn_l.addWidget(know_btn)
        layout.addLayout(btn_l)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.flipped = not self.flipped
        if self.flipped:
            self.hidden.show()
            self.hint.hide()
            self.setStyleSheet("""
                QFrame {
                    background:#0F2A1E;
                    border-radius:16px;
                    border:1px solid #10B981;
                }
            """)
        else:
            self.hidden.hide()
            self.hint.show()
            self.setStyleSheet("""
                QFrame {
                    background:#131C31;
                    border-radius:16px;
                    border:1px solid #1E293B;
                }
            """)


class VocabularyWidget(QWidget, DailyTaskMixin):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.init_daily_task()
        self.signals = VocabSignals()
        self.review_words = []
        self.current_index = 0
        self.correct_count = 0
        self._connect_signals()
        self._build()

    def _connect_signals(self):
        self.signals.word_added.connect(self._on_word_added)
        self.signals.review_loaded.connect(self._load_review)
        self.signals.error.connect(self._on_error)

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

        title = QLabel("📚  Vocabulary")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        left_l.addWidget(title)

        sub = QLabel("Bugungi so'zlar va spaced repetition")
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        left_l.addWidget(sub)

        # Progress
        prog_frame = QFrame()
        prog_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        prog_l = QHBoxLayout(prog_frame)
        prog_l.setContentsMargins(16, 12, 16, 12)
        prog_l.setSpacing(12)

        self.prog_lbl = QLabel("0 / 0 so'z")
        self.prog_lbl.setStyleSheet(
            "font-size:13px;color:#F1F5F9;font-weight:bold;"
        )
        self.prog_bar = QProgressBar()
        self.prog_bar.setValue(0)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setFixedHeight(6)
        self.prog_bar.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:3px;border:none;
            }
            QProgressBar::chunk {
                background:#10B981;border-radius:3px;
            }
        """)
        self.correct_lbl = QLabel("✓ 0")
        self.correct_lbl.setStyleSheet(
            "color:#10B981;font-size:13px;font-weight:bold;"
        )
        prog_l.addWidget(self.prog_lbl)
        prog_l.addWidget(self.prog_bar, 1)
        prog_l.addWidget(self.correct_lbl)
        left_l.addWidget(prog_frame)

        # Card stack
        self.card_stack = QStackedWidget()

        # 0: Boshlash
        start_w = QWidget()
        start_w.setStyleSheet("background:transparent;")
        start_l = QVBoxLayout(start_w)
        start_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_l.setSpacing(16)

        QLabel("📚").setParent(None)
        icon_l = QLabel("📚")
        icon_l.setStyleSheet("font-size:48px;border:none;")
        icon_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_t = QLabel("Bugungi takrorlashni boshlang")
        start_t.setStyleSheet(
            "font-size:16px;font-weight:bold;"
            "color:#F1F5F9;border:none;"
        )
        start_t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_s = QLabel(
            "So'zlarni ko'rib chiqing — Bildim yoki Bilmadim"
        )
        start_s.setStyleSheet(
            "font-size:13px;color:#94A3B8;border:none;"
        )
        start_s.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_btn = QPushButton("▶  Boshlash")
        start_btn.setFixedSize(160, 42)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
        """)
        start_btn.clicked.connect(self._start_review)

        start_l.addWidget(icon_l)
        start_l.addWidget(start_t)
        start_l.addWidget(start_s)
        start_l.addWidget(
            start_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.card_stack.addWidget(start_w)

        # 1: Flashcard
        self.card_container = QWidget()
        self.card_container.setStyleSheet("background:transparent;")
        self.card_container_l = QVBoxLayout(self.card_container)
        self.card_container_l.setContentsMargins(0, 0, 0, 0)
        self.card_stack.addWidget(self.card_container)

        # 2: Tugash
        finish_w = QWidget()
        finish_w.setStyleSheet("background:transparent;")
        finish_l = QVBoxLayout(finish_w)
        finish_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        finish_l.setSpacing(16)

        finish_icon = QLabel("🎉")
        finish_icon.setStyleSheet("font-size:48px;border:none;")
        finish_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.finish_title = QLabel("Sessiya tugadi!")
        self.finish_title.setStyleSheet(
            "font-size:20px;font-weight:bold;"
            "color:#10B981;border:none;"
        )
        self.finish_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.finish_sub = QLabel("")
        self.finish_sub.setStyleSheet(
            "font-size:14px;color:#94A3B8;border:none;"
        )
        self.finish_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        again_btn = QPushButton("🔄  Qayta boshlash")
        again_btn.setFixedSize(180, 42)
        again_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        again_btn.setStyleSheet("""
            QPushButton {
                background:#1E293B;color:#94A3B8;
                border:1px solid #334155;
                border-radius:8px;font-size:13px;
            }
            QPushButton:hover {
                background:#334155;color:#F1F5F9;
            }
        """)
        again_btn.clicked.connect(self._restart_review)

        finish_l.addWidget(finish_icon)
        finish_l.addWidget(self.finish_title)
        finish_l.addWidget(self.finish_sub)
        finish_l.addWidget(
            again_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.card_stack.addWidget(finish_w)

        left_l.addWidget(self.card_stack, 1)

        # ── O'NG ──
        right = QWidget()
        right.setFixedWidth(300)
        right.setStyleSheet(
            "background:#0F172A;"
            "border-left:1px solid #1E293B;"
        )
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(20, 24, 20, 24)
        right_l.setSpacing(14)

        # So'z qo'shish
        add_t = QLabel("So'z qo'shish")
        add_t.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#F1F5F9;"
        )
        right_l.addWidget(add_t)

        add_frame = QFrame()
        add_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        add_l = QVBoxLayout(add_frame)
        add_l.setContentsMargins(14, 14, 14, 14)
        add_l.setSpacing(8)

        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Inglizcha so'z...")
        self.word_input.setFixedHeight(36)
        self.word_input.setStyleSheet("""
            QLineEdit {
                background:#0F172A;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:6px;padding:6px 10px;
                font-size:13px;
            }
            QLineEdit:focus { border:1px solid #3B82F6; }
        """)

        self.uzbek_input = QLineEdit()
        self.uzbek_input.setPlaceholderText(
            "O'zbekcha (ixtiyoriy)..."
        )
        self.uzbek_input.setFixedHeight(36)
        self.uzbek_input.setStyleSheet("""
            QLineEdit {
                background:#0F172A;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:6px;padding:6px 10px;
                font-size:13px;
            }
            QLineEdit:focus { border:1px solid #3B82F6; }
        """)

        add_btn = QPushButton("+ Qo'shish")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:6px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
        """)
        add_btn.clicked.connect(self._add_word)

        add_l.addWidget(self.word_input)
        add_l.addWidget(self.uzbek_input)
        add_l.addWidget(add_btn)
        right_l.addWidget(add_frame)

        # Statistika
        stats_t = QLabel("Statistika")
        stats_t.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#F1F5F9;"
        )
        right_l.addWidget(stats_t)

        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        stats_l = QVBoxLayout(stats_frame)
        stats_l.setContentsMargins(14, 14, 14, 14)
        stats_l.setSpacing(10)

        self.stat_labels = {}
        for key, label, color in [
            ("total",    "Jami so'zlar",     "#F1F5F9"),
            ("new",      "Yangi",            "#94A3B8"),
            ("learning", "O'rganilmoqda",    "#3B82F6"),
            ("mastered", "O'zlashtirilgan",  "#10B981"),
            ("due",      "Bugun takrorlash", "#F59E0B"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{color};font-size:12px;border:none;"
            )
            val = QLabel("0")
            val.setStyleSheet(
                f"color:{color};font-size:12px;"
                "font-weight:bold;border:none;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            stats_l.addLayout(row)
            self.stat_labels[key] = val

        right_l.addWidget(stats_frame)

        # Word of the day
        wod_t = QLabel("Bugungi so'z")
        wod_t.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#F1F5F9;"
        )
        right_l.addWidget(wod_t)

        wod_frame = QFrame()
        wod_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:10px;
                border:1px solid #1E293B;
            }
        """)
        wod_l = QVBoxLayout(wod_frame)
        wod_l.setContentsMargins(14, 14, 14, 14)
        wod_l.setSpacing(6)

        self.wod_word = QLabel("—")
        self.wod_word.setStyleSheet(
            "font-size:20px;font-weight:bold;"
            "color:#3B82F6;border:none;"
        )
        self.wod_uzbek = QLabel("")
        self.wod_uzbek.setStyleSheet(
            "font-size:13px;color:#10B981;border:none;"
        )
        self.wod_def = QLabel("")
        self.wod_def.setStyleSheet(
            "font-size:11px;color:#94A3B8;border:none;"
        )
        self.wod_def.setWordWrap(True)

        wod_l.addWidget(self.wod_word)
        wod_l.addWidget(self.wod_uzbek)
        wod_l.addWidget(self.wod_def)
        right_l.addWidget(wod_frame)
        right_l.addStretch()

        main.addWidget(left, 1)
        main.addWidget(right)
        outer.addWidget(content, 1)

        self.refresh()

    # ── REVIEW ──────────────────────────────────────────────

    def _start_review(self):
        from src.vocabulary import VocabularyModule
        vm = VocabularyModule(self.db, self.ai)
        words = vm.get_daily_words(count=15)
        self.signals.review_loaded.emit(words)

    def _load_review(self, words):
        self.review_words = words
        self.current_index = 0
        self.correct_count = 0

        if not words:
            self.finish_title.setText(
                "✅ Bugun takrorlash kerak emas!"
            )
            self.finish_sub.setText(
                "Barcha so'zlar o'z vaqtida takrorlanadi"
            )
            self.card_stack.setCurrentIndex(2)
            return

        total = len(words)
        self.prog_lbl.setText(f"0 / {total} so'z")
        self.prog_bar.setValue(0)
        self.correct_lbl.setText("✓ 0")
        self._show_card(0)
        self.card_stack.setCurrentIndex(1)

    def _show_card(self, index):
        if index >= len(self.review_words):
            self._finish_review()
            return

        while self.card_container_l.count():
            item = self.card_container_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        word = self.review_words[index]
        card = FlashCard(
            word,
            on_know=lambda: self._answer(True),
            on_dont=lambda: self._answer(False)
        )
        self.card_container_l.addWidget(card)

        total = len(self.review_words)
        pct = int((index / total) * 100)
        self.prog_lbl.setText(f"{index} / {total} so'z")
        self.prog_bar.setValue(pct)

    def _answer(self, correct):
        if self.current_index >= len(self.review_words):
            return
        word = self.review_words[self.current_index]
        self.db.update_word_review(word["id"], correct)
        if correct:
            self.correct_count += 1
            self.correct_lbl.setText(f"✓ {self.correct_count}")
        self.current_index += 1
        self._show_card(self.current_index)

    def _finish_review(self):
        total = len(self.review_words)
        pct = int(
            self.correct_count / total * 100
        ) if total else 0
        self.finish_title.setText(
            f"🎉 {self.correct_count}/{total} to'g'ri!"
        )
        self.finish_sub.setText(
            f"To'g'ri: {pct}% — Zo'r ish! 💪"
        )
        self.prog_lbl.setText(f"{total} / {total} so'z")
        self.prog_bar.setValue(100)
        self.card_stack.setCurrentIndex(2)
        self.db.save_session(
            skill="Vocabulary",
            score=self.correct_count,
            max_score=total,
            duration=int(total * 0.5),
            details={
                "correct": self.correct_count,
                "total": total
            }
        )
        self.db.update_progress(
            "vocabulary",
            int(pct * 0.75),
        )
        self.complete_daily_task(int(pct * 0.75))
        self.refresh()

    def _restart_review(self):
        self.card_stack.setCurrentIndex(0)

    # ── SO'Z QO'SHISH ───────────────────────────────────────

    def _add_word(self):
        word = self.word_input.text().strip()
        if not word:
            return
        uzbek = self.uzbek_input.text().strip()
        self.word_input.clear()
        self.uzbek_input.clear()
        self.word_input.setPlaceholderText("⏳ Qo'shilmoqda...")

        def run():
            try:
                from src.vocabulary import VocabularyModule
                vm = VocabularyModule(self.db, self.ai)
                result = vm.add_word_manual(word, uzbek)
                self.signals.word_added.emit(result or {})
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_word_added(self, data):
        self.word_input.setPlaceholderText("Inglizcha so'z...")
        self.refresh()

    def _on_error(self, error):
        self.word_input.setPlaceholderText(f"❌ {error[:30]}")

    # ── REFRESH ─────────────────────────────────────────────

    def refresh(self):
        try:
            from src.vocabulary import VocabularyModule
            vm = VocabularyModule(self.db, self.ai)
            stats = vm.get_vocabulary_stats()
            self.stat_labels["total"].setText(
                str(stats.get("total_words", 0))
            )
            self.stat_labels["new"].setText(
                str(stats.get("new", 0))
            )
            self.stat_labels["learning"].setText(
                str(stats.get("learning", 0))
            )
            self.stat_labels["mastered"].setText(
                str(stats.get("mastered", 0))
            )
            self.stat_labels["due"].setText(
                str(stats.get("due_today", 0))
            )
            wod = vm.get_word_of_day()
            self.wod_word.setText(wod.get("word", "—"))
            self.wod_uzbek.setText(
                f"🇺🇿 {wod.get('uzbek', '')}"
            )
            self.wod_def.setText(
                wod.get("definition", "")
            )
        except Exception:
            pass
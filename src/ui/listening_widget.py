import os
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QRadioButton,
    QButtonGroup, QProgressBar, QSlider
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject


class ListeningSignals(QObject):
    transcript_ready = pyqtSignal(str)
    questions_ready = pyqtSignal(dict)
    audio_loaded = pyqtSignal(int)
    error = pyqtSignal(str)


class AudioPlayer(QFrame):
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.duration = 0
        self.position = 0
        self.audio_path = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_position)

        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        self.audio_title = QLabel("Audio yuklanmagan")
        self.audio_title.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        self.duration_lbl = QLabel("0:00")
        self.duration_lbl.setStyleSheet(
            "color:#475569;font-size:11px;border:none;"
        )
        title_row.addWidget(self.audio_title)
        title_row.addStretch()
        title_row.addWidget(self.duration_lbl)
        layout.addLayout(title_row)

        # Waveform simulatsiya
        self.wave_lbl = QLabel("━━━━━━━━━━━━━━━━━━━━")
        self.wave_lbl.setStyleSheet(
            "color:#1E293B;font-size:16px;"
            "letter-spacing:3px;border:none;"
        )
        self.wave_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.wave_lbl)

        # Progress slider
        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QSlider::groove:horizontal {
                background:#1E293B;
                height:4px;border-radius:2px;
            }
            QSlider::handle:horizontal {
                background:#3B82F6;
                width:12px;height:12px;
                margin:-4px 0;border-radius:6px;
            }
            QSlider::sub-page:horizontal {
                background:#3B82F6;border-radius:2px;
            }
        """)
        layout.addWidget(self.progress)

        # Time + Controls
        controls = QHBoxLayout()
        self.pos_lbl = QLabel("0:00")
        self.pos_lbl.setStyleSheet(
            "color:#475569;font-size:11px;border:none;"
        )

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.play_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:20px;
                font-size:14px;font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
            QPushButton:disabled {
                background:#1E293B;color:#475569;
            }
        """)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._toggle_play)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background:#1E293B;color:#94A3B8;
                border:1px solid #334155;
                border-radius:16px;font-size:12px;
            }
            QPushButton:hover { background:#334155; }
            QPushButton:disabled {
                background:#0F172A;color:#475569;
            }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)

        # Volume
        vol_lbl = QLabel("🔊")
        vol_lbl.setStyleSheet("border:none;font-size:14px;")
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background:#1E293B;height:3px;border-radius:1px;
            }
            QSlider::handle:horizontal {
                background:#94A3B8;width:10px;height:10px;
                margin:-3px 0;border-radius:5px;
            }
            QSlider::sub-page:horizontal {
                background:#3B82F6;border-radius:1px;
            }
        """)

        controls.addWidget(self.pos_lbl)
        controls.addStretch()
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.play_btn)
        controls.addStretch()
        controls.addWidget(vol_lbl)
        controls.addWidget(self.vol_slider)
        layout.addLayout(controls)

    def load_audio(self, path, title=""):
        self.audio_path = path
        self.audio_title.setText(
            title[:50] if title else os.path.basename(path)
        )
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            sound = pygame.mixer.Sound(path)
            self.duration = int(sound.get_length())
            mins = self.duration // 60
            secs = self.duration % 60
            self.duration_lbl.setText(f"{mins}:{secs:02d}")
        except Exception as e:
            self.duration = 180
            self.duration_lbl.setText("3:00")

    def _toggle_play(self):
        if self.is_playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        try:
            import pygame
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play()
            else:
                pygame.mixer.music.unpause()
            self.is_playing = True
            self.play_btn.setText("⏸")
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background:#F59E0B;color:white;
                    border:none;border-radius:20px;
                    font-size:14px;font-weight:bold;
                }
                QPushButton:hover { background:#D97706; }
            """)
            self.timer.start(500)
            self._animate_wave(True)
        except Exception as e:
            print(f"Audio xato: {e}")

    def _pause(self):
        try:
            import pygame
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.setText("▶")
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background:#3B82F6;color:white;
                    border:none;border-radius:20px;
                    font-size:14px;font-weight:bold;
                }
                QPushButton:hover { background:#2563EB; }
            """)
            self.timer.stop()
            self._animate_wave(False)
        except Exception as e:
            print(f"Audio xato: {e}")

    def _stop(self):
        try:
            import pygame
            pygame.mixer.music.stop()
            self.is_playing = False
            self.position = 0
            self.play_btn.setText("▶")
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background:#3B82F6;color:white;
                    border:none;border-radius:20px;
                    font-size:14px;font-weight:bold;
                }
                QPushButton:hover { background:#2563EB; }
            """)
            self.progress.setValue(0)
            self.pos_lbl.setText("0:00")
            self.timer.stop()
            self._animate_wave(False)
        except Exception as e:
            print(f"Audio xato: {e}")

    def _update_position(self):
        self.position += 0.5
        if self.duration > 0:
            pct = int((self.position / self.duration) * 100)
            self.progress.setValue(min(pct, 100))
            mins = int(self.position) // 60
            secs = int(self.position) % 60
            self.pos_lbl.setText(f"{mins}:{secs:02d}")

    def _animate_wave(self, active):
        waves = [
            "▁▃▅▇▅▃▁▃▅▇▅▃▁",
            "▃▅▇▅▃▁▃▅▇▅▃▁▃",
        ]
        if active:
            idx = int(self.position) % len(waves)
            self.wave_lbl.setText(waves[idx])
            self.wave_lbl.setStyleSheet(
                "color:#3B82F6;font-size:16px;"
                "letter-spacing:3px;border:none;"
            )
        else:
            self.wave_lbl.setText("━━━━━━━━━━━━━━━━━━━━")
            self.wave_lbl.setStyleSheet(
                "color:#1E293B;font-size:16px;"
                "letter-spacing:3px;border:none;"
            )


class ListeningQuestionItem(QFrame):
    def __init__(self, q_data, q_num):
        super().__init__()
        self.q_data = q_data
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
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        q_text = q_data.get("question", "")
        q_lbl = QLabel(f"{q_num}. {q_text}")
        q_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:12px;"
            "font-weight:bold;border:none;"
        )
        q_lbl.setWordWrap(True)
        layout.addWidget(q_lbl)

        options = q_data.get("options", {})
        if isinstance(options, dict):
            for key, val in options.items():
                rb = QRadioButton(f"{key})  {val}")
                rb.setStyleSheet("""
                    QRadioButton {
                        color:#CBD5E1;font-size:12px;
                        border:none;padding:3px;
                    }
                    QRadioButton:hover { color:#F1F5F9; }
                    QRadioButton::indicator {
                        width:13px;height:13px;
                    }
                    QRadioButton::indicator:checked {
                        background:#8B5CF6;
                        border-radius:6px;
                        border:2px solid #8B5CF6;
                    }
                    QRadioButton::indicator:unchecked {
                        background:transparent;
                        border-radius:6px;
                        border:2px solid #475569;
                    }
                """)
                rb.toggled.connect(
                    lambda chk, k=key: self._select(k)
                )
                self.btn_group.addButton(rb)
                layout.addWidget(rb)

    def _select(self, key):
        self.selected = key

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


class ListeningWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.signals = ListeningSignals()
        self.current_part = "Part3"
        self.question_items = []
        self.timer_seconds = 0
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._tick)
        self._connect_signals()
        self._build()

    def _connect_signals(self):
        self.signals.transcript_ready.connect(
            self._on_transcript
        )
        self.signals.questions_ready.connect(
            self._show_questions
        )
        self.signals.error.connect(self._show_error)

    def _build(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── CHAP ──
        left = QWidget()
        left.setStyleSheet("background:#0A0F1E;")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(24, 20, 12, 20)
        left_l.setSpacing(12)

        title = QLabel("🎧  Listening Practice")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#F1F5F9;"
        )
        left_l.addWidget(title)

        sub = QLabel(
            "Audio tinglang va savollarga javob bering"
        )
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        left_l.addWidget(sub)

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
        part_levels = {
            "Part1": "B1", "Part2": "B1",
            "Part3": "B2", "Part4": "B2",
            "Part5": "C1", "Part6": "C1"
        }
        for part in ["Part1","Part2","Part3",
                     "Part4","Part5","Part6"]:
            btn = QPushButton(part[-1])
            btn.setFixedSize(32, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                self._part_style(part == "Part3")
            )
            btn.clicked.connect(
                lambda chk, p=part: self._select_part(p)
            )
            self.part_btns[part] = btn
            part_l.addWidget(btn)

        part_l.addStretch()

        self.session_timer_lbl = QLabel("00:00")
        self.session_timer_lbl.setStyleSheet(
            "color:#8B5CF6;font-size:13px;font-weight:bold;"
        )
        part_l.addWidget(self.session_timer_lbl)
        left_l.addWidget(part_frame)

        # Audio player
        self.audio_player = AudioPlayer()
        left_l.addWidget(self.audio_player)

        # Eslatma
        note_frame = QFrame()
        note_frame.setStyleSheet("""
            QFrame {
                background:#1E1B4B;
                border-radius:8px;
                border:1px solid #3730A3;
            }
        """)
        note_l = QHBoxLayout(note_frame)
        note_l.setContentsMargins(14, 10, 14, 10)

        note_icon = QLabel("💡")
        note_icon.setStyleSheet("font-size:16px;border:none;")
        note_text = QLabel(
            "Audio tinglang → Savollarga javob bering → Tekshiring"
        )
        note_text.setStyleSheet(
            "color:#818CF8;font-size:12px;border:none;"
        )
        note_l.addWidget(note_icon)
        note_l.addWidget(note_text)
        note_l.addStretch()
        left_l.addWidget(note_frame)

        # Tugmalar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.load_btn = QPushButton("📂  Material yuklash")
        self.load_btn.setFixedHeight(42)
        self.load_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.load_btn.setStyleSheet("""
            QPushButton {
                background:#1E293B;color:#94A3B8;
                border:1px solid #334155;
                border-radius:8px;font-size:13px;
            }
            QPushButton:hover {
                background:#334155;color:#F1F5F9;
            }
        """)
        self.load_btn.clicked.connect(self._load_material)

        self.gen_btn = QPushButton("🤖  AI Audio")
        self.gen_btn.setFixedHeight(42)
        self.gen_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.gen_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
        """)
        self.gen_btn.clicked.connect(self._generate_questions)

        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.gen_btn)
        left_l.addLayout(btn_row)
        left_l.addStretch()

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
            "color:#8B5CF6;font-size:11px;"
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
                background:#8B5CF6;border-radius:2px;
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

        placeholder = QLabel(
            "Audio yuklang yoki\nAI Audio bosing"
        )
        placeholder.setStyleSheet(
            "color:#475569;font-size:13px;border:none;"
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.q_layout.addWidget(placeholder)
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

        self.res_score = QLabel("—")
        self.res_score.setStyleSheet(
            "font-size:26px;font-weight:bold;color:#8B5CF6;"
        )
        self.res_score.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.res_msg = QLabel("")
        self.res_msg.setStyleSheet(
            "font-size:12px;color:#94A3B8;"
        )
        self.res_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        res_l.addWidget(self.res_score)
        res_l.addWidget(self.res_msg)
        right_l.addWidget(self.result_frame)

        self.submit_btn = QPushButton("✅  Tekshirish")
        self.submit_btn.setFixedHeight(42)
        self.submit_btn.setEnabled(False)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background:#8B5CF6;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#7C3AED; }
            QPushButton:disabled {
                background:#1E293B;color:#475569;
            }
        """)
        self.submit_btn.clicked.connect(self._submit)
        right_l.addWidget(self.submit_btn)

        main.addWidget(left, 1)
        main.addWidget(right)

    # ── PART ────────────────────────────────────────────────

    def _part_style(self, active):
        if active:
            return (
                'QPushButton{'
                'background:#2D1B69;color:#8B5CF6;'
                'border:1px solid #8B5CF6;'
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
            b.setStyleSheet(self._part_style(p == part))
        self.current_part = part

    # ── MATERIAL YUKLASH ────────────────────────────────────

    def _load_material(self):
        self.load_btn.setEnabled(False)
        self.load_btn.setText("⏳ Yuklanmoqda...")

        def run():
            try:
                material = self.db.get_unused_material(
                    "listening", "audio"
                )
                if material:
                    path = material.get("file_path", "")
                    title = material.get("title", "Audio")
                    if os.path.exists(path):
                        self.audio_player.load_audio(path, title)
                        transcript = self._get_transcript(path)
                        self.signals.transcript_ready.emit(
                            transcript
                        )
                    else:
                        self.signals.error.emit(
                            "Audio fayl topilmadi"
                        )
                else:
                    self.signals.error.emit(
                        "Baza da audio material yo'q. "
                        "AI Audio tugmasini bosing."
                    )
            except Exception as e:
                self.signals.error.emit(str(e))
            finally:
                self.load_btn.setEnabled(True)
                self.load_btn.setText("📂  Material yuklash")

        threading.Thread(target=run, daemon=True).start()

    def _get_transcript(self, path):
        script = path.replace(
            ".mp3", ".txt"
        ).replace(".ogg", ".txt").replace(".wav", ".txt")
        if os.path.exists(script):
            with open(script, "r", encoding="utf-8") as f:
                return f.read()
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(path, language="en")
            return result["text"]
        except Exception:
            return ""

    # ── AI SAVOLLAR ─────────────────────────────────────────

    def _generate_questions(self):
        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("⏳ Generatsiya...")
        self.session_timer_lbl.setText("00:00")
        self.timer_seconds = 0
        self.session_timer.start(1000)

        def run():
            try:
                from config.settings import READING_RULES

                part_rules = {
                    "Part1": {"level":"B1","questions":5,
                              "type":"sentence_completion"},
                    "Part2": {"level":"B1","questions":5,
                              "type":"multiple_choice"},
                    "Part3": {"level":"B2","questions":6,
                              "type":"matching"},
                    "Part4": {"level":"B2","questions":6,
                              "type":"note_completion"},
                    "Part5": {"level":"C1","questions":4,
                              "type":"multiple_choice"},
                    "Part6": {"level":"C1","questions":4,
                              "type":"summary_completion"},
                }

                rule = part_rules.get(self.current_part, {})
                level = rule.get("level", "B2")
                count = rule.get("questions", 5)
                q_type = rule.get("type", "multiple_choice")

                # Sample transcript
                transcript = self.ai._send(
                    "Generate a B2-level listening transcript.",
                    f"Write a 200-word conversation about "
                    f"technology and education for {level} level."
                )

                questions = self.ai.generate_listening_questions(
                    transcript=transcript,
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
            finally:
                self.gen_btn.setEnabled(True)
                self.gen_btn.setText("🤖  AI Audio")

        threading.Thread(target=run, daemon=True).start()

    def _on_transcript(self, transcript):
        if transcript:
            self._generate_from_transcript(transcript)

    def _generate_from_transcript(self, transcript):
        part_rules = {
            "Part1": {"level":"B1","questions":5},
            "Part2": {"level":"B1","questions":5},
            "Part3": {"level":"B2","questions":6},
            "Part4": {"level":"B2","questions":6},
            "Part5": {"level":"C1","questions":4},
            "Part6": {"level":"C1","questions":4},
        }
        rule = part_rules.get(self.current_part, {})
        level = rule.get("level", "B2")
        count = rule.get("questions", 5)

        def run():
            try:
                questions = self.ai.generate_listening_questions(
                    transcript=transcript,
                    part_name=self.current_part,
                    level=level,
                    question_type="multiple_choice",
                    count=count
                )
                questions["part"] = self.current_part
                questions["level"] = level
                questions["q_type"] = "multiple_choice"
                self.signals.questions_ready.emit(questions)
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    # ── SAVOLLARNI KO'RSATISH ───────────────────────────────

    def _show_questions(self, data):
        questions = data.get("questions", [])
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
            self.q_layout.addStretch()
            return

        colors = {"B1":"#10B981","B2":"#8B5CF6","C1":"#3B82F6"}
        color = colors.get(level, "#94A3B8")
        badge = QLabel(f"{part} • {level}")
        badge.setStyleSheet(
            f"background:{color}22;color:{color};"
            f"border:1px solid {color}44;"
            f"border-radius:6px;padding:3px 10px;"
            f"font-size:11px;font-weight:bold;"
        )
        badge.setFixedHeight(24)
        self.q_layout.addWidget(badge)

        for i, q in enumerate(questions):
            item = ListeningQuestionItem(q, i + 1)
            self.q_layout.addWidget(item)
            self.question_items.append((item, q))

        self.q_layout.addStretch()

        total = len(questions)
        self.q_count_lbl.setText(f"0/{total}")
        self.q_progress.setValue(0)
        self.submit_btn.setEnabled(True)
        self.result_frame.hide()

    # ── TEKSHIRISH ──────────────────────────────────────────

    def _submit(self):
        self.submit_btn.setEnabled(False)
        self.session_timer.stop()

        correct = 0
        total = len(self.question_items)

        for item, q_data in self.question_items:
            correct_ans = q_data.get("answer", "")
            is_correct = item.show_result(correct_ans)
            if is_correct:
                correct += 1

        pct = int(correct / total * 100) if total else 0

        if pct >= 60:
            msg = "✅ O'tdingiz!"
            color = "#10B981"
        else:
            msg = "⚠️ Yana mashq kerak"
            color = "#F59E0B"

        self.res_score.setText(f"{correct}/{total} ({pct}%)")
        self.res_score.setStyleSheet(
            f"font-size:26px;font-weight:bold;color:{color};"
        )
        self.res_msg.setText(msg)
        self.result_frame.show()

        self.q_count_lbl.setText(f"{total}/{total}")
        self.q_progress.setValue(100)

        self.db.save_session(
            skill="Listening",
            score=correct,
            max_score=total,
            duration=self.timer_seconds // 60,
            details={
                "part": self.current_part,
                "correct": correct,
                "total": total
            }
        )
        self.db.update_progress(
            "listening", int(pct * 0.75)
        )

    def _show_error(self, error):
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
        self.session_timer_lbl.setText(f"{m:02d}:{s:02d}")

    def refresh(self):
        pass
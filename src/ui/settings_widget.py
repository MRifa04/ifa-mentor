import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QComboBox,
    QGridLayout
)
from PyQt6.QtCore import Qt
from config.settings import (
    USER_NAME, CURRENT_LEVEL,
    TARGET_LEVEL, AI_ENGINE,
    GEMINI_MODEL, APP_VERSION
)


class SectionFrame(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(14)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;border:none;"
        )
        self.layout.addWidget(title_lbl)

    def add_row(self, label, widget):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        lbl.setFixedWidth(160)
        row.addWidget(lbl)
        row.addWidget(widget, 1)
        self.layout.addLayout(row)

    def add_widget(self, widget):
        self.layout.addWidget(widget)


class SettingsWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
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
        title = QLabel("⚙️  Sozlamalar")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        sub = QLabel("IFA Mentor shaxsiy sozlamalari")
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # ── Foydalanuvchi ──
        user_section = SectionFrame("FOYDALANUVCHI")

        self.name_input = QLineEdit(USER_NAME)
        self.name_input.setStyleSheet(self._input_style())
        self.name_input.setFixedHeight(36)
        user_section.add_row("Ism:", self.name_input)

        level_combo = QComboBox()
        level_combo.addItems(["A1", "A2", "B1", "B2", "C1"])
        level_combo.setCurrentText(CURRENT_LEVEL)
        level_combo.setStyleSheet(self._combo_style())
        level_combo.setFixedHeight(36)
        user_section.add_row("Hozirgi daraja:", level_combo)

        target_combo = QComboBox()
        target_combo.addItems(["B1", "B2", "C1"])
        target_combo.setCurrentText(TARGET_LEVEL)
        target_combo.setStyleSheet(self._combo_style())
        target_combo.setFixedHeight(36)
        user_section.add_row("Maqsad daraja:", target_combo)

        self.date_input = QLineEdit("2026-10-01")
        self.date_input.setStyleSheet(self._input_style())
        self.date_input.setFixedHeight(36)
        user_section.add_row("Imtihon sanasi:", self.date_input)

        self.study_time_input = QLineEdit("90")
        self.study_time_input.setStyleSheet(self._input_style())
        self.study_time_input.setFixedHeight(36)
        user_section.add_row(
            "Kunlik o'qish (min):", self.study_time_input
        )

        layout.addWidget(user_section)

        # ── AI Engine ──
        ai_section = SectionFrame("AI ENGINE")

        ai_combo = QComboBox()
        ai_combo.addItems(["gemini", "claude", "ollama"])
        ai_combo.setCurrentText(AI_ENGINE)
        ai_combo.setStyleSheet(self._combo_style())
        ai_combo.setFixedHeight(36)
        ai_section.add_row("AI Engine:", ai_combo)

        model_combo = QComboBox()
        model_combo.addItems([
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "claude-sonnet-4-6",
            "llama3"
        ])
        model_combo.setCurrentText(GEMINI_MODEL)
        model_combo.setStyleSheet(self._combo_style())
        model_combo.setFixedHeight(36)
        ai_section.add_row("Model:", model_combo)

        # AI status
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background:#0F172A;
                border-radius:8px;
                border:1px solid #1E293B;
            }
        """)
        status_l = QHBoxLayout(status_frame)
        status_l.setContentsMargins(12, 10, 12, 10)

        status_dot = QLabel("●")
        status_dot.setStyleSheet(
            "color:#F59E0B;font-size:12px;border:none;"
        )
        status_text = QLabel(
            f"AI: {AI_ENGINE.upper()} — API kaliti kerak"
        )
        status_text.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        status_l.addWidget(status_dot)
        status_l.addWidget(status_text)
        status_l.addStretch()
        ai_section.add_widget(status_frame)

        layout.addWidget(ai_section)

        # ── API Kalitlar ──
        api_section = SectionFrame("API KALITLAR")

        self.gemini_input = QLineEdit()
        self.gemini_input.setPlaceholderText(
            "AIza... (aistudio.google.com)"
        )
        self.gemini_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.gemini_input.setStyleSheet(self._input_style())
        self.gemini_input.setFixedHeight(36)
        api_section.add_row("Gemini API:", self.gemini_input)

        self.claude_input = QLineEdit()
        self.claude_input.setPlaceholderText(
            "sk-ant-... (console.anthropic.com)"
        )
        self.claude_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.claude_input.setStyleSheet(self._input_style())
        self.claude_input.setFixedHeight(36)
        api_section.add_row("Claude API:", self.claude_input)

        self.telegram_input = QLineEdit()
        self.telegram_input.setPlaceholderText(
            "Bot token (t.me/BotFather)"
        )
        self.telegram_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.telegram_input.setStyleSheet(self._input_style())
        self.telegram_input.setFixedHeight(36)
        api_section.add_row(
            "Telegram Bot:", self.telegram_input
        )

        # Saqlash tugmasi
        save_api_btn = QPushButton("💾  API Kalitlarni Saqlash")
        save_api_btn.setFixedHeight(38)
        save_api_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_api_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#2563EB; }
        """)
        save_api_btn.clicked.connect(self._save_api_keys)
        api_section.add_widget(save_api_btn)

        layout.addWidget(api_section)

        # ── Telegram Kanallar ──
        tg_section = SectionFrame("TELEGRAM KANALLAR")

        channels = self.db.get_active_channels()
        if channels:
            for ch in channels:
                row_frame = QFrame()
                row_frame.setStyleSheet("""
                    QFrame {
                        background:#0F172A;
                        border-radius:8px;
                        border:1px solid #1E293B;
                    }
                """)
                row_l = QHBoxLayout(row_frame)
                row_l.setContentsMargins(12, 8, 12, 8)

                name = QLabel(ch.get("channel_name", ""))
                name.setStyleSheet(
                    "color:#F1F5F9;font-size:12px;border:none;"
                )
                skill = QLabel(ch.get("skill", "").upper())
                skill.setStyleSheet(
                    "color:#3B82F6;font-size:11px;border:none;"
                )
                total = QLabel(
                    f"{ch.get('total_materials', 0)} material"
                )
                total.setStyleSheet(
                    "color:#475569;font-size:11px;border:none;"
                )

                row_l.addWidget(name)
                row_l.addStretch()
                row_l.addWidget(skill)
                row_l.addWidget(total)
                tg_section.add_widget(row_frame)
        else:
            no_ch = QLabel("Hech qanday kanal qo'shilmagan")
            no_ch.setStyleSheet(
                "color:#475569;font-size:12px;border:none;"
            )
            tg_section.add_widget(no_ch)

        # Kanal qo'shish
        ch_frame = QFrame()
        ch_frame.setStyleSheet("""
            QFrame {
                background:#0F172A;
                border-radius:8px;
                border:1px solid #1E293B;
            }
        """)
        ch_l = QVBoxLayout(ch_frame)
        ch_l.setContentsMargins(12, 12, 12, 12)
        ch_l.setSpacing(8)

        ch_title = QLabel("Yangi kanal qo'shish:")
        ch_title.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        ch_l.addWidget(ch_title)

        self.ch_name = QLineEdit()
        self.ch_name.setPlaceholderText("@kanal_nomi")
        self.ch_name.setStyleSheet(self._input_style())
        self.ch_name.setFixedHeight(32)

        self.ch_id = QLineEdit()
        self.ch_id.setPlaceholderText("Kanal ID: -100...")
        self.ch_id.setStyleSheet(self._input_style())
        self.ch_id.setFixedHeight(32)

        self.ch_skill = QComboBox()
        self.ch_skill.addItems([
            "mixed", "listening", "reading",
            "writing", "speaking", "vocabulary"
        ])
        self.ch_skill.setStyleSheet(self._combo_style())
        self.ch_skill.setFixedHeight(32)

        ch_add_btn = QPushButton("+ Qo'shish")
        ch_add_btn.setFixedHeight(32)
        ch_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ch_add_btn.setStyleSheet("""
            QPushButton {
                background:#1E3A5F;color:#3B82F6;
                border:1px solid #3B82F6;
                border-radius:6px;font-size:12px;
            }
            QPushButton:hover { background:#1E293B; }
        """)
        ch_add_btn.clicked.connect(self._add_channel)

        ch_l.addWidget(self.ch_name)
        ch_l.addWidget(self.ch_id)
        ch_l.addWidget(self.ch_skill)
        ch_l.addWidget(ch_add_btn)
        tg_section.add_widget(ch_frame)

        layout.addWidget(tg_section)

        # ── Ma'lumotlar ──
        data_section = SectionFrame("MA'LUMOTLAR")

        reset_btn = QPushButton("🗑️  Progressni tozalash")
        reset_btn.setFixedHeight(38)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton {
                background:#2D1B1B;color:#EF4444;
                border:1px solid #EF4444;
                border-radius:8px;font-size:13px;
            }
            QPushButton:hover { background:#3D2020; }
        """)
        data_section.add_widget(reset_btn)

        version_lbl = QLabel(f"IFA Mentor v{APP_VERSION}")
        version_lbl.setStyleSheet(
            "color:#475569;font-size:11px;border:none;"
        )
        data_section.add_widget(version_lbl)

        layout.addWidget(data_section)
        layout.addStretch()

        scroll.setWidget(content)
        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.addWidget(scroll)

    # ── AMALLAR ─────────────────────────────────────────────

    def _save_api_keys(self):
        gemini = self.gemini_input.text().strip()
        claude = self.claude_input.text().strip()
        telegram = self.telegram_input.text().strip()

        env_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    )
                )
            ),
            ".env"
        )

        lines = []
        if gemini:
            lines.append(f"GEMINI_API_KEY={gemini}")
        if claude:
            lines.append(f"ANTHROPIC_API_KEY={claude}")
        if telegram:
            lines.append(f"TELEGRAM_BOT_TOKEN={telegram}")

        if lines:
            with open(env_path, "w") as f:
                f.write("\n".join(lines))
            self.gemini_input.setPlaceholderText(
                "✅ Saqlandi!"
            )
            self.gemini_input.clear()
            self.claude_input.clear()
            self.telegram_input.clear()

    def _add_channel(self):
        name = self.ch_name.text().strip()
        ch_id = self.ch_id.text().strip()
        skill = self.ch_skill.currentText()

        if name and ch_id:
            self.db.add_channel(name, ch_id, skill)
            self.ch_name.clear()
            self.ch_id.clear()
            self.ch_name.setPlaceholderText(
                f"✅ {name} qo'shildi!"
            )

    # ── STYLE HELPERS ────────────────────────────────────────

    def _input_style(self):
        return """
            QLineEdit {
                background:#0F172A;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:6px;padding:6px 10px;
                font-size:12px;
            }
            QLineEdit:focus { border:1px solid #3B82F6; }
        """

    def _combo_style(self):
        return """
            QComboBox {
                background:#0F172A;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:6px;padding:6px 10px;
                font-size:12px;
            }
            QComboBox:focus { border:1px solid #3B82F6; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#131C31;color:#F1F5F9;
                border:1px solid #1E293B;
                selection-background-color:#1E3A5F;
            }
        """

    def refresh(self):
        pass
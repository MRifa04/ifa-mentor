import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QComboBox,
    QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from config.settings import (
    USER_NAME, CURRENT_LEVEL,
    TARGET_LEVEL, AI_ENGINE,
    GEMINI_MODEL, APP_VERSION,
    DAILY_STUDY_TIME, TARGET_DATE,
)
from src.user_profile import get_profile


class SettingsSignals(QObject):
    sync_done = pyqtSignal(dict)
    sync_error = pyqtSignal(str)
    sync_progress = pyqtSignal(str)


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
    def __init__(
        self,
        db,
        ai,
        on_profile_saved=None,
        on_sync_complete=None,
    ):
        super().__init__()
        self.db = db
        self.ai = ai
        self.on_profile_saved = on_profile_saved
        self.on_sync_complete = on_sync_complete
        self.signals = SettingsSignals()
        self.signals.sync_done.connect(self._on_sync_done)
        self.signals.sync_error.connect(self._on_sync_error)
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

        profile = get_profile(self.db)
        self.profile_banner = QLabel(
            f"📋 Aktiv profil: {profile['name']} | "
            f"{profile['current_level']} → {profile['target_level']} | "
            f"{profile['daily_minutes']} min/kun | "
            f"Imtihon: {profile['target_date']}"
        )
        self.profile_banner.setWordWrap(True)
        self.profile_banner.setStyleSheet(
            "color:#10B981;font-size:12px;"
            "background:#0F2A1E;border:1px solid #10B981;"
            "border-radius:8px;padding:10px;"
        )
        layout.addWidget(self.profile_banner)

        # ── Foydalanuvchi ──
        user_section = SectionFrame("FOYDALANUVCHI")
        user = self.db.get_user() or {}

        self.name_input = QLineEdit(
            user.get("name", USER_NAME)
        )
        self.name_input.setStyleSheet(self._input_style())
        self.name_input.setFixedHeight(36)
        user_section.add_row("Ism:", self.name_input)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["A1", "A2", "B1", "B2", "C1"])
        self.level_combo.setCurrentText(
            user.get("current_level", CURRENT_LEVEL)
        )
        self.level_combo.setStyleSheet(self._combo_style())
        self.level_combo.setFixedHeight(36)
        user_section.add_row("Hozirgi daraja:", self.level_combo)

        self.target_combo = QComboBox()
        self.target_combo.addItems(["B1", "B2", "C1"])
        self.target_combo.setCurrentText(
            user.get("target_level", TARGET_LEVEL)
        )
        self.target_combo.setStyleSheet(self._combo_style())
        self.target_combo.setFixedHeight(36)
        user_section.add_row("Maqsad daraja:", self.target_combo)

        self.date_input = QLineEdit(
            user.get("target_date", TARGET_DATE)
        )
        self.date_input.setStyleSheet(self._input_style())
        self.date_input.setFixedHeight(36)
        user_section.add_row("Imtihon sanasi:", self.date_input)

        self.study_time_input = QLineEdit(
            str(user.get("daily_minutes", DAILY_STUDY_TIME))
        )
        self.study_time_input.setStyleSheet(self._input_style())
        self.study_time_input.setFixedHeight(36)
        user_section.add_row(
            "Kunlik o'qish (min):", self.study_time_input
        )

        save_profile_btn = QPushButton(
            "💾  Profilni Saqlash"
        )
        save_profile_btn.setFixedHeight(38)
        save_profile_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        save_profile_btn.setStyleSheet("""
            QPushButton {
                background:#10B981;color:white;
                border:none;border-radius:8px;
                font-size:13px;font-weight:bold;
            }
            QPushButton:hover { background:#059669; }
        """)
        save_profile_btn.clicked.connect(
            self._save_profile
        )
        user_section.add_widget(save_profile_btn)

        layout.addWidget(user_section)

        # ── Ovoz yordamchisi ──
        voice_section = SectionFrame("OVOZ YORDAMCHISI")
        try:
            from src.ui.Voice.speech import SpeechEngine
            speech = SpeechEngine()
            stt_ok = speech.stt_available
            tts_ok = speech.tts_available
            if stt_ok and tts_ok:
                voice_status = "✅ Mikrofon va ovoz tayyor"
                voice_color = "#10B981"
            elif stt_ok or tts_ok:
                voice_status = (
                    "⚠️ Qisman tayyor "
                    f"(STT: {'✓' if stt_ok else '✗'}, "
                    f"TTS: {'✓' if tts_ok else '✗'})"
                )
                voice_color = "#F59E0B"
            else:
                voice_status = (
                    "❌ Ovoz kutubxonalari topilmadi"
                )
                voice_color = "#EF4444"
        except Exception:
            voice_status = "❌ Ovoz moduli yuklanmadi"
            voice_color = "#EF4444"

        voice_lbl = QLabel(voice_status)
        voice_lbl.setStyleSheet(
            f"color:{voice_color};font-size:12px;border:none;"
        )
        voice_section.add_widget(voice_lbl)
        layout.addWidget(voice_section)

        # ── AI Engine ──
        ai_section = SectionFrame("AI ENGINE")

        ai_combo = QComboBox()
        ai_combo.addItems(["gemini", "claude", "ollama"])
        ai_combo.setCurrentText(AI_ENGINE)
        ai_combo.setStyleSheet(self._combo_style())
        ai_combo.setFixedHeight(36)
        self.ai_combo = ai_combo
        ai_section.add_row("AI Engine:", ai_combo)

        model_combo = QComboBox()
        model_combo.addItems([
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "claude-sonnet-4-6",
            "llama3",
        ])
        model_combo.setCurrentText(GEMINI_MODEL)
        model_combo.setStyleSheet(self._combo_style())
        model_combo.setFixedHeight(36)
        self.model_combo = model_combo
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
        self.ai_status_dot = status_dot
        self.ai_status_text = QLabel(
            self._ai_status_message()
        )
        self.ai_status_text.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        status_l.addWidget(status_dot)
        status_l.addWidget(self.ai_status_text)
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
            "Bot token (ixtiyoriy, t.me/BotFather)"
        )
        self.telegram_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.telegram_input.setStyleSheet(self._input_style())
        self.telegram_input.setFixedHeight(36)
        api_section.add_row(
            "Telegram Bot:", self.telegram_input
        )

        self.tg_api_id_input = QLineEdit()
        self.tg_api_id_input.setPlaceholderText(
            "API ID (my.telegram.org)"
        )
        self.tg_api_id_input.setStyleSheet(self._input_style())
        self.tg_api_id_input.setFixedHeight(36)
        api_section.add_row("Telegram API ID:", self.tg_api_id_input)

        self.tg_api_hash_input = QLineEdit()
        self.tg_api_hash_input.setPlaceholderText("API Hash")
        self.tg_api_hash_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.tg_api_hash_input.setStyleSheet(self._input_style())
        self.tg_api_hash_input.setFixedHeight(36)
        api_section.add_row(
            "Telegram API Hash:", self.tg_api_hash_input
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

        self.tg_status_lbl = QLabel()
        self.tg_status_lbl.setWordWrap(True)
        self.tg_status_lbl.setStyleSheet(
            "color:#94A3B8;font-size:11px;border:none;"
        )
        tg_section.add_widget(self.tg_status_lbl)
        self._update_tg_status()
        self.tg_section = tg_section
        self.tg_channels_container = QWidget()
        self.tg_channels_container.setStyleSheet(
            "background:transparent;border:none;"
        )
        self.tg_channels_layout = QVBoxLayout(
            self.tg_channels_container
        )
        self.tg_channels_layout.setContentsMargins(0, 0, 0, 0)
        self.tg_channels_layout.setSpacing(6)
        tg_section.add_widget(self.tg_channels_container)
        self._render_channels()

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
        self.ch_id.setPlaceholderText(
            "@username yoki -100... (username yetarli)"
        )
        self.ch_id.setStyleSheet(self._input_style())
        self.ch_id.setFixedHeight(32)

        self.ch_skill = QComboBox()
        self.ch_skill.addItems([
            "listening", "reading", "writing", "speaking",
            "vocabulary", "grammar", "tenses", "mock", "mixed",
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

        preset_btn = QPushButton("📋 Shablon kanallar")
        preset_btn.setFixedHeight(32)
        preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preset_btn.setStyleSheet("""
            QPushButton {
                background:#1E293B;color:#94A3B8;
                border:1px solid #334155;
                border-radius:6px;font-size:12px;
            }
            QPushButton:hover { background:#334155;color:#F1F5F9; }
        """)
        preset_btn.clicked.connect(self._add_preset_channels)

        self.sync_limit_input = QLineEdit("2500")
        self.sync_limit_input.setPlaceholderText(
            "Mock kanal uchun 2500 tavsiya etiladi"
        )
        self.sync_limit_input.setStyleSheet(self._input_style())
        self.sync_limit_input.setFixedHeight(32)

        sync_btn = QPushButton("🔄  Kanallarni sinxronlash")
        sync_btn.setFixedHeight(32)
        sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sync_btn.setStyleSheet("""
            QPushButton {
                background:#10B981;color:white;
                border:none;border-radius:6px;font-size:12px;
            }
            QPushButton:hover { background:#059669; }
        """)
        sync_btn.clicked.connect(self._sync_channels)

        ch_l.addWidget(self.ch_name)
        ch_l.addWidget(self.ch_id)
        ch_l.addWidget(self.ch_skill)
        ch_l.addWidget(self.sync_limit_input)
        ch_l.addWidget(ch_add_btn)
        ch_l.addWidget(preset_btn)
        ch_l.addWidget(sync_btn)
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
        reset_btn.clicked.connect(self._reset_progress)
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

    def _env_path(self):
        return os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    )
                )
            ),
            ".env",
        )

    def _save_profile(self):
        daily_text = self.study_time_input.text().strip()
        try:
            daily_minutes = int(daily_text)
        except ValueError:
            daily_minutes = DAILY_STUDY_TIME

        self.db.update_user(
            name=self.name_input.text().strip(),
            current_level=self.level_combo.currentText(),
            target_level=self.target_combo.currentText(),
            target_date=self.date_input.text().strip(),
            daily_minutes=daily_minutes,
        )
        self.name_input.setPlaceholderText(
            "Profil saqlandi!"
        )

        if self.on_profile_saved:
            self.on_profile_saved()

        QMessageBox.information(
            self,
            "Tayyor",
            "Profil saqlandi.",
        )

    def _reset_progress(self):
        answer = QMessageBox.question(
            self,
            "Progressni tozalash",
            "Barcha sessiyalar va progress tarixi "
            "o'chirilsinmi? So'zlar bazasi saqlanadi.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.clear_study_progress()
        if self.on_profile_saved:
            self.on_profile_saved()
        QMessageBox.information(
            self,
            "Tayyor",
            "Progress tozalandi.",
        )

    def _save_api_keys(self):
        gemini = self.gemini_input.text().strip()
        claude = self.claude_input.text().strip()
        telegram = self.telegram_input.text().strip()
        tg_api_id = self.tg_api_id_input.text().strip()
        tg_api_hash = self.tg_api_hash_input.text().strip()
        engine = self.ai_combo.currentText().strip()
        model = self.model_combo.currentText().strip()

        env_path = self._env_path()
        lines = []

        if gemini:
            lines.append(f"GEMINI_API_KEY={gemini}")
        if claude:
            lines.append(f"ANTHROPIC_API_KEY={claude}")
        if telegram:
            lines.append(f"TELEGRAM_BOT_TOKEN={telegram}")
        if tg_api_id:
            lines.append(f"TELEGRAM_API_ID={tg_api_id}")
        if tg_api_hash:
            lines.append(f"TELEGRAM_API_HASH={tg_api_hash}")
        if engine:
            lines.append(f"AI_ENGINE={engine}")
        if model:
            lines.append(f"GEMINI_MODEL={model}")

        if lines:
            existing = {}
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, val = line.split("=", 1)
                            existing[key] = val

            for line in lines:
                key, val = line.split("=", 1)
                existing[key] = val

            with open(env_path, "w", encoding="utf-8") as f:
                for key, val in existing.items():
                    f.write(f"{key}={val}\n")

            if hasattr(self.ai, "reload_api_config"):
                self.ai.reload_api_config()

            self.gemini_input.setPlaceholderText(
                "Saqlandi! AI yangilandi."
            )
            self.gemini_input.clear()
            self.claude_input.clear()
            self.telegram_input.clear()
            self.tg_api_id_input.clear()
            self.tg_api_hash_input.clear()
            self._update_tg_status()
            self.refresh()
            QMessageBox.information(
                self,
                "Tayyor",
                "API kalitlar saqlandi va AI yangilandi.",
            )

    def _render_channels(self):
        while self.tg_channels_layout.count():
            item = self.tg_channels_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        channels = self.db.get_active_channels()
        if not channels:
            no_ch = QLabel("Hech qanday kanal qo'shilmagan")
            no_ch.setStyleSheet(
                "color:#475569;font-size:12px;border:none;"
            )
            self.tg_channels_layout.addWidget(no_ch)
            return

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
            self.tg_channels_layout.addWidget(row_frame)

    def _update_tg_status(self):
        from src.telegram_loader import TelegramLoader

        loader = TelegramLoader(self.db)
        status = loader.status()
        ready = loader.is_ready()
        color = "#10B981" if ready else "#F59E0B"
        self.tg_status_lbl.setText(status)
        self.tg_status_lbl.setStyleSheet(
            f"color:{color};font-size:11px;border:none;"
        )

    def _add_preset_channels(self):
        from src.channel_presets import CHANNEL_PRESETS

        added = 0
        for preset in CHANNEL_PRESETS:
            name = preset["channel_name"]
            if name.startswith("@your_"):
                continue
            self.db.add_channel(
                preset["channel_name"],
                preset["channel_id"],
                preset["skill"],
            )
            added += 1

        if added:
            self._render_channels()
            QMessageBox.information(
                self,
                "Shablonlar",
                f"{added} ta kanal qo'shildi.",
            )
        else:
            QMessageBox.information(
                self,
                "Shablonlar",
                "Shablon kanallarni src/channel_presets.py da "
                "o'z kanallaringiz bilan yangilang, keyin qayta bosing.",
            )

    def _sync_channels(self):
        import threading
        from src.telegram_loader import TelegramLoader

        try:
            limit = int(self.sync_limit_input.text().strip() or "100")
        except ValueError:
            limit = 100

        loader = TelegramLoader(
            self.db,
            on_progress=lambda msg: self.signals.sync_progress.emit(msg),
        )

        if not loader.is_ready():
            QMessageBox.warning(self, "Telegram", loader.status())
            return

        def run():
            try:
                result = loader.sync(limit_per_channel=limit)
                self.signals.sync_done.emit(result)
            except Exception as exc:
                self.signals.sync_error.emit(str(exc))

        threading.Thread(target=run, daemon=True).start()
        QMessageBox.information(
            self,
            "Sinxronizatsiya",
            f"{len(self.db.get_active_channels())} ta kanal "
            f"sinxronlanmoqda (har biri ≤{limit} post)...",
        )

    def _on_sync_done(self, result):
        total = result.get("total", 0)
        self._render_channels()
        self._update_tg_status()
        if self.on_sync_complete:
            self.on_sync_complete()
        QMessageBox.information(
            self,
            "Tayyor",
            f"Sinxronizatsiya tugadi.\n"
            f"Yangi materiallar: {total} ta",
        )

    def _on_sync_error(self, message):
        QMessageBox.critical(
            self,
            "Telegram xato",
            message,
        )

    def _add_channel(self):
        name = self.ch_name.text().strip()
        ch_id = self.ch_id.text().strip()
        skill = self.ch_skill.currentText()

        if not name:
            name = ch_id

        if ch_id:
            self.db.add_channel(name, ch_id, skill)
            self.ch_name.clear()
            self.ch_id.clear()
            self.ch_name.setPlaceholderText(
                f"✅ {name} qo'shildi!"
            )
            self._render_channels()

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

    def _ai_status_message(self):
        import os

        engine = AI_ENGINE.upper()
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")

        if AI_ENGINE == "gemini":
            if gemini_key:
                return f"AI: {engine} — API kalit topildi ✅"
            return f"AI: {engine} — GEMINI_API_KEY kerak"

        if AI_ENGINE == "claude":
            if claude_key:
                return f"AI: {engine} — API kalit topildi ✅"
            return f"AI: {engine} — ANTHROPIC_API_KEY kerak"

        if AI_ENGINE == "ollama":
            return f"AI: {engine} — localhost:11434"

        return f"AI: {engine}"

    def refresh(self):
        profile = get_profile(self.db)
        if hasattr(self, "profile_banner"):
            self.profile_banner.setText(
                f"📋 Aktiv profil: {profile['name']} | "
                f"{profile['current_level']} → "
                f"{profile['target_level']} | "
                f"{profile['daily_minutes']} min/kun | "
                f"Imtihon: {profile['target_date']}"
            )

        if hasattr(self, "tg_channels_layout"):
            self._render_channels()

        if hasattr(self, "tg_status_lbl"):
            self._update_tg_status()

        if hasattr(self, "ai_status_text"):
            self.ai_status_text.setText(
                self._ai_status_message()
            )

        if hasattr(self, "ai_status_dot"):
            ready = "topildi" in self._ai_status_message()
            color = "#10B981" if ready else "#F59E0B"
            self.ai_status_dot.setStyleSheet(
                f"color:{color};font-size:12px;border:none;"
            )
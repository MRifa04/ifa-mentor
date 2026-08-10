import os
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QComboBox,
    QFileDialog, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject


class LibrarySignals(QObject):
    materials_loaded = pyqtSignal(list)
    material_added = pyqtSignal()
    error = pyqtSignal(str)


class MaterialCard(QFrame):
    def __init__(self, material):
        super().__init__()
        skill = material.get("skill", "mixed")
        file_type = material.get("file_type", "pdf")
        title = material.get("title", "Unknown")
        level = material.get("level", "B2")
        channel = material.get("source_channel", "")
        is_used = material.get("is_used", 0)

        skill_colors = {
            "listening":  "#8B5CF6",
            "reading":    "#10B981",
            "writing":    "#C084FC",
            "speaking":   "#3B82F6",
            "vocabulary": "#4ADE80",
            "mixed":      "#F59E0B"
        }
        type_icons = {
            "audio": "🎵",
            "pdf":   "📄",
            "txt":   "📝",
            "test":  "📋",
            "other": "📁"
        }
        color = skill_colors.get(skill, "#94A3B8")
        icon = type_icons.get(file_type, "📁")

        self.setStyleSheet(f"""
            QFrame {{
                background:#131C31;
                border-radius:10px;
                border:1px solid {'#1E3A5F' if not is_used else '#1E293B'};
                border-left:3px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            "font-size:18px;border:none;"
        )
        icon_lbl.setFixedWidth(28)

        title_lbl = QLabel(
            title[:45] + "..." if len(title) > 45 else title
        )
        title_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:12px;"
            "font-weight:bold;border:none;"
        )

        header.addWidget(icon_lbl)
        header.addWidget(title_lbl, 1)
        layout.addLayout(header)

        # Tags
        tags = QHBoxLayout()
        tags.setSpacing(6)

        skill_badge = QLabel(skill.upper())
        skill_badge.setStyleSheet(
            f"background:{color}22;color:{color};"
            f"border:1px solid {color}44;"
            f"border-radius:4px;padding:1px 6px;"
            f"font-size:10px;font-weight:bold;"
        )

        level_badge = QLabel(level)
        level_badge.setStyleSheet(
            "background:#1E293B;color:#94A3B8;"
            "border-radius:4px;padding:1px 6px;"
            "font-size:10px;border:none;"
        )

        used_badge = QLabel(
            "✅ Ishlatilgan" if is_used else "🆕 Yangi"
        )
        used_badge.setStyleSheet(
            f"color:{'#475569' if is_used else '#10B981'};"
            "font-size:10px;border:none;"
        )

        tags.addWidget(skill_badge)
        tags.addWidget(level_badge)
        tags.addWidget(used_badge)
        tags.addStretch()
        layout.addLayout(tags)

        if channel and channel != "manual":
            ch_lbl = QLabel(f"📡 {channel}")
            ch_lbl.setStyleSheet(
                "color:#475569;font-size:10px;border:none;"
            )
            layout.addWidget(ch_lbl)


class LibraryWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.signals = LibrarySignals()
        self.all_materials = []
        self.filtered = []
        self._connect_signals()
        self._build()

    def _connect_signals(self):
        self.signals.materials_loaded.connect(
            self._show_materials
        )
        self.signals.material_added.connect(
            self.refresh
        )
        self.signals.error.connect(self._on_error)

    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── HEADER ──
        header_w = QWidget()
        header_w.setStyleSheet("background:#0A0F1E;")
        header_l = QVBoxLayout(header_w)
        header_l.setContentsMargins(28, 20, 28, 16)
        header_l.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("🗂️  Library")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        add_btn = QPushButton("+ Fayl qo'shish")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background:#3B82F6;color:white;
                border:none;border-radius:8px;
                font-size:12px;font-weight:bold;
                padding:0 16px;
            }
            QPushButton:hover { background:#2563EB; }
        """)
        add_btn.clicked.connect(self._add_file)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(add_btn)
        header_l.addLayout(title_row)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "🔍 Qidirish..."
        )
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background:#131C31;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:8px;padding:6px 12px;
                font-size:13px;
            }
            QLineEdit:focus { border:1px solid #3B82F6; }
        """)
        self.search_input.textChanged.connect(
            self._filter_materials
        )

        # Skill filter
        self.skill_filter = QComboBox()
        self.skill_filter.addItems([
            "Barcha skilllar",
            "listening", "reading",
            "writing", "speaking",
            "vocabulary", "mixed"
        ])
        self.skill_filter.setFixedHeight(36)
        self.skill_filter.setFixedWidth(150)
        self.skill_filter.setStyleSheet("""
            QComboBox {
                background:#131C31;color:#F1F5F9;
                border:1px solid #1E293B;
                border-radius:8px;padding:6px 10px;
                font-size:12px;
            }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#131C31;color:#F1F5F9;
                border:1px solid #1E293B;
                selection-background-color:#1E3A5F;
            }
        """)
        self.skill_filter.currentTextChanged.connect(
            self._filter_materials
        )

        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Barcha turlar",
            "audio", "pdf", "txt", "test"
        ])
        self.type_filter.setFixedHeight(36)
        self.type_filter.setFixedWidth(130)
        self.type_filter.setStyleSheet(
            self.skill_filter.styleSheet()
        )
        self.type_filter.currentTextChanged.connect(
            self._filter_materials
        )

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "Hammasi", "Yangi", "Ishlatilgan"
        ])
        self.status_filter.setFixedHeight(36)
        self.status_filter.setFixedWidth(120)
        self.status_filter.setStyleSheet(
            self.skill_filter.styleSheet()
        )
        self.status_filter.currentTextChanged.connect(
            self._filter_materials
        )

        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.skill_filter)
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(self.status_filter)
        header_l.addLayout(filter_row)

        # Stats row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(16)
        self.total_lbl = QLabel("Jami: 0")
        self.total_lbl.setStyleSheet(
            "color:#94A3B8;font-size:12px;"
        )
        self.new_lbl = QLabel("Yangi: 0")
        self.new_lbl.setStyleSheet(
            "color:#10B981;font-size:12px;"
        )
        self.used_lbl = QLabel("Ishlatilgan: 0")
        self.used_lbl.setStyleSheet(
            "color:#475569;font-size:12px;"
        )
        self.stats_row.addWidget(self.total_lbl)
        self.stats_row.addWidget(self.new_lbl)
        self.stats_row.addWidget(self.used_lbl)
        self.stats_row.addStretch()
        header_l.addLayout(self.stats_row)

        main.addWidget(header_w)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background:#1E293B;")
        main.addWidget(div)

        # ── CONTENT ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{border:none;background:#0A0F1E;}"
        )

        self.content_w = QWidget()
        self.content_w.setStyleSheet("background:#0A0F1E;")
        self.content_l = QVBoxLayout(self.content_w)
        self.content_l.setContentsMargins(28, 16, 28, 24)
        self.content_l.setSpacing(12)

        # Placeholder
        self.placeholder = QLabel(
            "📂 Material topilmadi\n\n"
            "Telegram kanaldan sync qiling yoki\n"
            "fayl qo'shish tugmasini bosing"
        )
        self.placeholder.setStyleSheet(
            "color:#475569;font-size:14px;border:none;"
        )
        self.placeholder.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.content_l.addWidget(self.placeholder)
        self.content_l.addStretch()

        scroll.setWidget(self.content_w)
        main.addWidget(scroll, 1)

        self.refresh()

    # ── MATERIALLARNI YUKLASH ────────────────────────────────

    def refresh(self):
        def run():
            try:
                conn = self.db.connect()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM materials
                    ORDER BY created_at DESC
                """)
                rows = [dict(r) for r in cursor.fetchall()]
                self.db.close()
                self.signals.materials_loaded.emit(rows)
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _show_materials(self, materials):
        self.all_materials = materials
        self._update_stats(materials)
        self._render_materials(materials)

    def _update_stats(self, materials):
        total = len(materials)
        new = sum(
            1 for m in materials
            if not m.get("is_used", 0)
        )
        used = total - new
        self.total_lbl.setText(f"Jami: {total}")
        self.new_lbl.setText(f"Yangi: {new}")
        self.used_lbl.setText(f"Ishlatilgan: {used}")

    def _render_materials(self, materials):
        # Eski widgetlarni o'chirish
        while self.content_l.count():
            item = self.content_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not materials:
            self.placeholder = QLabel(
                "📂 Material topilmadi\n\n"
                "Telegram kanaldan sync qiling yoki\n"
                "fayl qo'shish tugmasini bosing"
            )
            self.placeholder.setStyleSheet(
                "color:#475569;font-size:14px;border:none;"
            )
            self.placeholder.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.content_l.addWidget(self.placeholder)
            self.content_l.addStretch()
            return

        # Grid layout
        grid = QGridLayout()
        grid.setSpacing(10)

        for i, material in enumerate(materials):
            card = MaterialCard(material)
            grid.addWidget(card, i // 3, i % 3)

        grid_w = QWidget()
        grid_w.setStyleSheet("background:transparent;")
        grid_w.setLayout(grid)
        self.content_l.addWidget(grid_w)
        self.content_l.addStretch()

    # ── FILTER ──────────────────────────────────────────────

    def _filter_materials(self):
        search = self.search_input.text().lower()
        skill = self.skill_filter.currentText()
        ftype = self.type_filter.currentText()
        status = self.status_filter.currentText()

        filtered = self.all_materials

        if search:
            filtered = [
                m for m in filtered
                if search in m.get("title", "").lower()
                or search in m.get("skill", "").lower()
            ]

        if skill != "Barcha skilllar":
            filtered = [
                m for m in filtered
                if m.get("skill") == skill
            ]

        if ftype != "Barcha turlar":
            filtered = [
                m for m in filtered
                if m.get("file_type") == ftype
            ]

        if status == "Yangi":
            filtered = [
                m for m in filtered
                if not m.get("is_used", 0)
            ]
        elif status == "Ishlatilgan":
            filtered = [
                m for m in filtered
                if m.get("is_used", 0)
            ]

        self._update_stats(filtered)
        self._render_materials(filtered)

    # ── FAYL QO'SHISH ───────────────────────────────────────

    def _add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Fayl tanlang",
            "",
            "Barcha fayllar (*.pdf *.txt *.mp3 "
            "*.ogg *.wav *.json);;PDF (*.pdf);;"
            "Audio (*.mp3 *.ogg *.wav);;"
            "Text (*.txt);;Test (*.json)"
        )

        if not file_path:
            return

        # Skill tanlash
        skill_dialog = QWidget(self)
        skill_dialog.setWindowFlags(
            Qt.WindowType.Dialog
        )

        from src.telegram_loader import TelegramLoader
        loader = TelegramLoader(self.db)

        # Fayl turini aniqlash
        filename = os.path.basename(file_path)
        file_type = loader.detect_file_type(filename)
        skill = loader.detect_skill(filename)
        level = loader.detect_level(filename)

        def run():
            try:
                result = loader.add_manual_material(
                    file_path, skill, level
                )
                if result:
                    self.signals.material_added.emit()
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_error(self, error):
        err_lbl = QLabel(f"❌ {error[:80]}")
        err_lbl.setStyleSheet(
            "color:#EF4444;font-size:12px;"
        )
        self.content_l.addWidget(err_lbl)
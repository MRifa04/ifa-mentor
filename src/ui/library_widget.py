import os
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QComboBox,
    QFileDialog, QGridLayout, QInputDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from src.telegram_grouping import group_materials_for_library


class LibrarySignals(QObject):
    materials_loaded = pyqtSignal(list)
    material_added = pyqtSignal()
    review_loaded = pyqtSignal(int)
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
            "grammar":    "#F472B6",
            "tenses":     "#FB923C",
            "mock":       "#EF4444",
            "mixed":      "#F59E0B"
        }
        type_icons = {
            "audio": "🎵",
            "pdf":   "📄",
            "txt":   "📝",
            "test":  "📋",
            "text":  "💬",
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
            f"background:{color};"
            f"color:#FFFFFF;"
            f"border:none;"
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

        preview = material.get("content_text") or ""
        if preview and file_type == "text":
            snippet = preview[:120] + ("..." if len(preview) > 120 else "")
            preview_lbl = QLabel(snippet)
            preview_lbl.setWordWrap(True)
            preview_lbl.setStyleSheet(
                "color:#64748B;font-size:10px;border:none;"
            )
            layout.addWidget(preview_lbl)


class MaterialSetCard(QFrame):
    """Mock to'plam: PDF + Part 1-6 audiolar tartibda."""

    def __init__(self, set_data):
        super().__init__()
        title = set_data.get("title", "To'plam")
        skill = set_data.get("skill", "mock")
        level = set_data.get("level", "B2")
        items = set_data.get("items", [])

        skill_colors = {
            "mock": "#EF4444",
            "listening": "#8B5CF6",
            "reading": "#10B981",
            "mixed": "#F59E0B",
        }
        color = skill_colors.get(skill, "#3B82F6")

        self.setStyleSheet(f"""
            QFrame {{
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
                border-left:4px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title_lbl = QLabel(f"📦  {title}")
        title_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:14px;font-weight:bold;border:none;"
        )
        count_lbl = QLabel(
            set_data.get("summary") or f"{len(items)} fayl"
        )
        count_lbl.setStyleSheet(
            "color:#64748B;font-size:11px;border:none;"
        )
        skill_badge = QLabel(skill.upper())
        skill_badge.setStyleSheet(
            f"background:{color};color:#FFF;border:none;"
            f"border-radius:4px;padding:2px 8px;font-size:10px;"
        )
        level_badge = QLabel(level)
        level_badge.setStyleSheet(
            "background:#1E293B;color:#94A3B8;border:none;"
            "border-radius:4px;padding:2px 8px;font-size:10px;"
        )
        header.addWidget(title_lbl, 1)
        header.addWidget(skill_badge)
        header.addWidget(level_badge)
        header.addWidget(count_lbl)
        layout.addLayout(header)

        for item in items:
            ft = item.get("file_type", "")
            role = item.get("material_role", "")
            icon = {"pdf": "📄", "audio": "🎵", "txt": "📝"}.get(ft, "📁")
            name = item.get("title", "")
            part = item.get("part_order") or ""
            part_txt = f"Part {part}" if part else ""
            role_txt = f"[{role}] " if role else ""
            row = QLabel(
                f"  {icon}  {role_txt}{part_txt + ' — ' if part_txt else ''}{name}"
            )
            row.setStyleSheet(
                "color:#CBD5E1;font-size:11px;border:none;padding:2px 0;"
            )
            layout.addWidget(row)


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
        self.signals.review_loaded.connect(self._on_review_loaded)
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
            "vocabulary", "grammar",
            "tenses", "mock", "mixed"
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
            "audio", "pdf", "txt", "test", "text"
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

        self.view_filter = QComboBox()
        self.view_filter.addItems([
            "To'plamlar",
            "Ro'yxat",
        ])
        self.view_filter.setFixedHeight(36)
        self.view_filter.setFixedWidth(120)
        self.view_filter.setStyleSheet(
            self.skill_filter.styleSheet()
        )
        self.view_filter.currentTextChanged.connect(
            self._filter_materials
        )

        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.skill_filter)
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(self.view_filter)
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

        self.review_banner = QFrame()
        self.review_banner.setStyleSheet("""
            QFrame {
                background:#2D1F0F;
                border:1px solid #F59E0B;
                border-radius:8px;
            }
        """)
        review_l = QHBoxLayout(self.review_banner)
        review_l.setContentsMargins(12, 8, 12, 8)
        self.review_lbl = QLabel("Review queue: 0")
        self.review_lbl.setStyleSheet(
            "color:#FCD34D;font-size:12px;border:none;"
        )
        review_btn = QPushButton("Ko'rish")
        review_btn.setFixedHeight(28)
        review_btn.setStyleSheet("""
            QPushButton {
                background:#F59E0B;color:#1E293B;
                border:none;border-radius:6px;
                font-size:11px;font-weight:bold;padding:0 12px;
            }
            QPushButton:hover { background:#D97706; }
        """)
        review_btn.clicked.connect(self._show_review_queue)
        review_l.addWidget(self.review_lbl, 1)
        review_l.addWidget(review_btn)
        header_l.addWidget(self.review_banner)
        self.review_banner.hide()

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
                rows = self.db.get_all_materials()
                review = self.db.get_mock_review_queue("pending")
                self.signals.materials_loaded.emit(rows)
                self.signals.review_loaded.emit(len(review))
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_review_loaded(self, count):
        if count > 0:
            self.review_lbl.setText(
                f"Review queue: {count} ta mock tekshiruvi kerak"
            )
            self.review_banner.show()
        else:
            self.review_banner.hide()

    def _show_review_queue(self):
        items = self.db.get_mock_review_queue("pending")
        if not items:
            QMessageBox.information(
                self, "Review", "Tekshiruv navbatida hech narsa yo'q."
            )
            return

        lines = []
        for item in items[:15]:
            conf = int((item.get("confidence") or 0) * 100)
            lines.append(
                f"- {item.get('set_title')} ({conf}%): "
                f"{item.get('reason', '')[:60]}"
            )
        text = "\n".join(lines)
        if len(items) > 15:
            text += f"\n... va yana {len(items) - 15} ta"

        answer = QMessageBox.question(
            self,
            "Review Queue",
            text + "\n\nBirinchi elementni tasdiqlash?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.db.resolve_review_item(items[0]["id"], "approved")
            self.refresh()

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

        view_mode = "sets"
        if hasattr(self, "view_filter"):
            view_mode = (
                "sets"
                if self.view_filter.currentText() == "To'plamlar"
                else "list"
            )

        if view_mode == "sets":
            sets_list, standalone = group_materials_for_library(materials)
            for set_data in sets_list:
                card = MaterialSetCard(set_data)
                self.content_l.addWidget(card)

            if standalone:
                sep = QLabel("— Alohida fayllar —")
                sep.setStyleSheet(
                    "color:#475569;font-size:12px;border:none;"
                    "padding:12px 0 4px 0;"
                )
                self.content_l.addWidget(sep)
                grid = QGridLayout()
                grid.setSpacing(10)
                for i, material in enumerate(standalone):
                    grid.addWidget(MaterialCard(material), i // 3, i % 3)
                grid_w = QWidget()
                grid_w.setStyleSheet("background:transparent;")
                grid_w.setLayout(grid)
                self.content_l.addWidget(grid_w)
        else:
            grid = QGridLayout()
            grid.setSpacing(10)
            visible = [
                m for m in materials
                if not (
                    m.get("category") == "post"
                    and m.get("file_type") == "text"
                )
            ]
            for i, material in enumerate(visible):
                grid.addWidget(MaterialCard(material), i // 3, i % 3)
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
                or search in (m.get("set_title") or "").lower()
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

        skill, ok = QInputDialog.getItem(
            self,
            "Skill tanlang",
            "Material qaysi skill uchun?",
            [
                "reading",
                "listening",
                "writing",
                "speaking",
                "vocabulary",
            ],
            0,
            False,
        )
        if not ok:
            return

        level, ok = QInputDialog.getItem(
            self,
            "Daraja tanlang",
            "CEFR darajasi:",
            ["B1", "B2", "C1"],
            1,
            False,
        )
        if not ok:
            return

        from src.telegram_loader import TelegramLoader
        loader = TelegramLoader(self.db)

        filename = os.path.basename(file_path)
        file_type = loader.detect_file_type(filename)
        if skill == "reading" and file_type not in ("pdf", "txt"):
            skill = loader.detect_skill(filename)

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
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon
from src.ui.styles import MAIN_STYLE, SKILL_ICONS
from config.settings import USER_NAME, APP_NAME

class Sidebar(QWidget):
    def __init__(self, on_navigate):
        super().__init__()
        self.setObjectName("sidebar")
        self.on_navigate = on_navigate
        self.active_btn = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setStyleSheet(
            "border-bottom: 1px solid #1E293B;"
            "padding-bottom: 16px;"
        )
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 24, 20, 16)

        logo = QLabel("⬡ IFA\nMENTOR")
        logo.setObjectName("logo_label")
        logo.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
            "color: #F1F5F9; letter-spacing: 2px;"
        )

        logo_sub = QLabel("AI English Coach")
        logo_sub.setObjectName("logo_sub")
        logo_sub.setStyleSheet(
            "font-size: 10px; color: #3B82F6;"
            "letter-spacing: 1px;"
        )

        logo_layout.addWidget(logo)
        logo_layout.addWidget(logo_sub)
        layout.addWidget(logo_frame)

        # Nav buttons
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        nav_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 12, 0, 12)
        nav_layout.setSpacing(2)

        self.nav_buttons = {}
        pages = [
            "Home", "Study DNA", "Reading",
            "Listening", "Speaking", "Writing",
            "Vocabulary", "Library", "Mock Exams",
            "Progress", "Statistics", "Settings"
        ]

        for page in pages:
            icon = SKILL_ICONS.get(page, "•")
            btn = QPushButton(f"  {icon}  {page}")
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94A3B8;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    text-align: left;
                    font-size: 13px;
                    margin: 1px 8px;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: #F1F5F9;
                }
            """)
            btn.clicked.connect(
                lambda checked, p=page: self._navigate(p)
            )
            self.nav_buttons[page] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        layout.addWidget(nav_scroll)

        # User info
        user_frame = QFrame()
        user_frame.setStyleSheet(
            "border-top: 1px solid #1E293B; padding: 12px;"
        )
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 12, 16, 12)

        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 24px;")

        user_info = QVBoxLayout()
        name_lbl = QLabel(USER_NAME)
        name_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #F1F5F9;"
        )
        level_lbl = QLabel("B1 → B2")
        level_lbl.setStyleSheet(
            "font-size: 11px; color: #3B82F6;"
        )
        user_info.addWidget(name_lbl)
        user_info.addWidget(level_lbl)

        user_layout.addWidget(avatar)
        user_layout.addLayout(user_info)
        layout.addWidget(user_frame)

        # Default: Home
        self._navigate("Home")

    def _navigate(self, page):
        # Oldingi tugmani reset
        if self.active_btn:
            self.active_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94A3B8;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    text-align: left;
                    font-size: 13px;
                    margin: 1px 8px;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: #F1F5F9;
                }
            """)

        # Yangi tugmani faollashtirish
        btn = self.nav_buttons.get(page)
        if btn:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E3A5F;
                    color: #3B82F6;
                    border: none;
                    border-left: 3px solid #3B82F6;
                    border-radius: 8px;
                    padding: 8px 16px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: bold;
                    margin: 1px 8px;
                }
            """)
            self.active_btn = btn

        self.on_navigate(page)


class MainWindow(QMainWindow):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self._setup_window()
        self._build_ui()
        self._navigate("Home")

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} — CEFR B2 Coach")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self.setStyleSheet(MAIN_STYLE)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self._navigate)
        main_layout.addWidget(self.sidebar)

        # Content area
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(
            "background-color: #0A0F1E;"
        )
        main_layout.addWidget(self.stack)

        # Sahifalarni import va qo'shish
        self._init_pages()

    def _init_pages(self):
        from src.ui.dashboard_widget import DashboardWidget
        from src.ui.placeholder_widget import PlaceholderWidget

        self.pages = {}

        # Dashboard
        self.pages["Home"] = DashboardWidget(self.db, self.ai)
        self.stack.addWidget(self.pages["Home"])

        # Qolgan sahifalar (placeholder)
        other_pages = [
            "Study DNA", "Reading", "Listening",
            "Speaking", "Writing", "Vocabulary",
            "Library", "Mock Exams", "Progress",
            "Statistics", "Settings"
        ]
        for page in other_pages:
            widget = PlaceholderWidget(page)
            self.pages[page] = widget
            self.stack.addWidget(widget)

    def _navigate(self, page):
        widget = self.pages.get(page)
        if widget:
            self.stack.setCurrentWidget(widget)
            # Dashboard refresh
            if page == "Home" and hasattr(widget, 'refresh'):
                widget.refresh()
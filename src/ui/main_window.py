import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from src.ui.styles import MAIN_STYLE, SKILL_ICONS
from config.settings import USER_NAME, APP_NAME


class Sidebar(QWidget):
    def __init__(self, on_navigate):
        super().__init__()
        self.setObjectName("sidebar")
        self.on_navigate = on_navigate
        self.active_btn = None
        self.nav_buttons = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setStyleSheet(
            "border-bottom: 1px solid #1E293B;"
        )
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 24, 20, 16)

        logo = QLabel("⬡ IFA MENTOR")
        logo.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
            "color: #F1F5F9; letter-spacing: 2px;"
            "border: none;"
        )
        logo_sub = QLabel("AI English Coach")
        logo_sub.setStyleSheet(
            "font-size: 10px; color: #3B82F6;"
            "letter-spacing: 1px; border: none;"
        )
        logo_layout.addWidget(logo)
        logo_layout.addWidget(logo_sub)
        layout.addWidget(logo_frame)

        # Nav scroll
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

        pages = [
            "Home", "Study DNA", "Reading",
            "Listening", "Speaking", "Writing",
            "Vocabulary", "Library", "Mock Exams",
            "Progress", "Statistics", "Settings"
        ]

        for page in pages:
            icon = SKILL_ICONS.get(page, "•")
            btn = QPushButton(f"  {icon}  {page}")
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._btn_style(False))
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
            "border-top: 1px solid #1E293B;"
        )
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 12, 16, 12)

        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 22px; border: none;")

        info_layout = QVBoxLayout()
        name_lbl = QLabel(USER_NAME)
        name_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold;"
            "color: #F1F5F9; border: none;"
        )
        level_lbl = QLabel("B1 → B2")
        level_lbl.setStyleSheet(
            "font-size: 11px; color: #3B82F6; border: none;"
        )
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(level_lbl)
        info_layout.setSpacing(2)

        user_layout.addWidget(avatar)
        user_layout.addLayout(info_layout)
        layout.addWidget(user_frame)

    def _btn_style(self, active):
        if active:
            return """
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
            """
        return """
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
        """

    def _navigate(self, page):
        if self.active_btn:
            self.active_btn.setStyleSheet(self._btn_style(False))
        btn = self.nav_buttons.get(page)
        if btn:
            btn.setStyleSheet(self._btn_style(True))
            self.active_btn = btn
        self.on_navigate(page)

    def set_active(self, page):
        self._navigate(page)


class MainWindow(QMainWindow):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.pages = {}
        self._setup_window()
        self._build_ui()
        # Sahifalar tayyor bo'lgach navigate
        self.sidebar.set_active("Home")

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

        # Sidebar — navigate ni keyinroq ulaymiz
        self.sidebar = Sidebar(self._navigate)
        main_layout.addWidget(self.sidebar)

        # Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #0A0F1E;")
        main_layout.addWidget(self.stack)

        # Sahifalar
        self._init_pages()

    def _init_pages(self):
        from src.ui.dashboard_widget import DashboardWidget
        from src.ui.placeholder_widget import PlaceholderWidget

        # Dashboard
        dashboard = DashboardWidget(self.db, self.ai)
        self.pages["Home"] = dashboard
        self.stack.addWidget(dashboard)

        # Placeholder sahifalar
        others = [
            "Study DNA", "Reading", "Listening",
            "Speaking", "Writing", "Vocabulary",
            "Library", "Mock Exams", "Progress",
            "Statistics", "Settings"
        ]
        for page in others:
            w = PlaceholderWidget(page)
            self.pages[page] = w
            self.stack.addWidget(w)

    def _navigate(self, page):
        widget = self.pages.get(page)
        if widget:
            self.stack.setCurrentWidget(widget)
            if hasattr(widget, 'refresh'):
                widget.refresh()
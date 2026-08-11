import sys
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
        self.on_navigate = on_navigate
        self.active_btn = None
        self.nav_buttons = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        logo_frame = QFrame()
        logo_frame.setStyleSheet(
            'border-bottom:1px solid #1E293B;'
        )
        ll = QVBoxLayout(logo_frame)
        ll.setContentsMargins(20, 20, 20, 16)
        ll.setSpacing(4)
        logo = QLabel('IFA MENTOR')
        logo.setStyleSheet(
            'font-size:20px;font-weight:bold;'
            'color:#F1F5F9;border:none;'
            'letter-spacing:2px;'
        )
        sub = QLabel('AI English Coach')
        sub.setStyleSheet(
            'font-size:12px;color:#3B82F6;border:none;'
        )
        ll.addWidget(logo)
        ll.addWidget(sub)
        layout.addWidget(logo_frame)

        nav_w = QWidget()
        nav_w.setStyleSheet('background:transparent;')
        nav_l = QVBoxLayout(nav_w)
        nav_l.setContentsMargins(8, 16, 8, 16)
        nav_l.setSpacing(4)

        groups = [
            {"label": "ASOSIY",
             "pages": ["Home", "Study DNA", "Maqsad"]},
            {"label": "SKILLLAR",
             "pages": ["Reading", "Listening",
                       "Speaking", "Writing", "Vocabulary"]},
            {"label": "IMTIHON",
             "pages": ["Library", "Mock Exams"]},
            {"label": "TAHLIL",
             "pages": ["Progress", "Statistics"]},
            {"label": "SOZLAMA",
             "pages": ["Settings"]},
        ]

        for group in groups:
            grp_lbl = QLabel(group["label"])
            grp_lbl.setStyleSheet(
                'color:#334155;font-size:10px;'
                'font-weight:bold;letter-spacing:1px;'
                'border:none;padding:4px 12px 2px 12px;'
            )
            nav_l.addWidget(grp_lbl)

            for page in group["pages"]:
                icon = SKILL_ICONS.get(page, '○')
                btn = QPushButton(f' {icon}   {page}')
                btn.setFixedHeight(44)
                btn.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )
                btn.setStyleSheet(self._style(False))
                btn.clicked.connect(
                    lambda chk, p=page: self._nav(p)
                )
                self.nav_buttons[page] = btn
                nav_l.addWidget(btn)

            spacer = QFrame()
            spacer.setFixedHeight(8)
            spacer.setStyleSheet(
                'background:transparent;border:none;'
            )
            nav_l.addWidget(spacer)

        nav_l.addStretch()

        sc = QScrollArea()
        sc.setWidget(nav_w)
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        sc.setStyleSheet(
            'QScrollArea{border:none;background:transparent;}'
        )
        layout.addWidget(sc)

        uf = QFrame()
        uf.setStyleSheet(
            'border-top:1px solid #1E293B;'
            'background:#0F172A;'
        )
        ul = QHBoxLayout(uf)
        ul.setContentsMargins(16, 14, 16, 14)
        ul.setSpacing(12)

        av_frame = QFrame()
        av_frame.setFixedSize(40, 40)
        av_frame.setStyleSheet(
            'background:#1E3A5F;'
            'border-radius:20px;border:none;'
        )
        av_l = QVBoxLayout(av_frame)
        av_l.setContentsMargins(0, 0, 0, 0)
        av = QLabel('I')
        av.setStyleSheet(
            'font-size:16px;font-weight:bold;'
            'color:#3B82F6;border:none;'
        )
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av_l.addWidget(av)

        il = QVBoxLayout()
        il.setSpacing(2)
        nl = QLabel(USER_NAME)
        nl.setStyleSheet(
            'font-size:14px;font-weight:bold;'
            'color:#F1F5F9;border:none;'
        )
        lv = QLabel('B1 → B2')
        lv.setStyleSheet(
            'font-size:11px;color:#3B82F6;border:none;'
        )
        il.addWidget(nl)
        il.addWidget(lv)

        ul.addWidget(av_frame)
        ul.addLayout(il)
        ul.addStretch()

        badge = QLabel('B1')
        badge.setStyleSheet(
            'background:#1E3A5F;color:#3B82F6;'
            'border-radius:6px;padding:3px 8px;'
            'font-size:12px;font-weight:bold;border:none;'
        )
        ul.addWidget(badge)
        layout.addWidget(uf)

    def _style(self, active):
        if active:
            return (
                'QPushButton{'
                'background:#1E3A5F;color:#3B82F6;'
                'border:none;'
                'border-left:3px solid #3B82F6;'
                'border-radius:8px;'
                'padding:10px 16px;'
                'text-align:left;font-size:14px;'
                'font-weight:bold;}'
            )
        return (
            'QPushButton{'
            'background:transparent;color:#94A3B8;'
            'border:none;border-radius:8px;'
            'padding:10px 16px;text-align:left;'
            'font-size:14px;}'
            'QPushButton:hover{'
            'background:#1E293B;color:#F1F5F9;}'
        )

    def _nav(self, page):
        if self.active_btn:
            self.active_btn.setStyleSheet(self._style(False))
        btn = self.nav_buttons.get(page)
        if btn:
            btn.setStyleSheet(self._style(True))
            self.active_btn = btn
        self.on_navigate(page)

    def activate(self, page):
        self._nav(page)


class MainWindow(QMainWindow):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.pages = {}
        self.setWindowTitle(f'{APP_NAME} - CEFR B2 Coach')
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self.setStyleSheet(MAIN_STYLE)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet('background:#0A0F1E;')
        self._load_pages()
        self.sidebar = Sidebar(self._navigate)
        self.sidebar.setFixedWidth(240)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        self.sidebar.activate('Home')

    def _load_pages(self):
        from src.ui.dashboard_widget import DashboardWidget
        from src.ui.speaking_widget import SpeakingWidget
        from src.ui.progress_widget import ProgressWidget
        from src.ui.writing_widget import WritingWidget
        from src.ui.vocabulary_widget import VocabularyWidget
        from src.ui.settings_widget import SettingsWidget
        from src.ui.reading_widget import ReadingWidget
        from src.ui.listening_widget import ListeningWidget
        from src.ui.study_dna_widget import StudyDNAWidget
        from src.ui.mock_exams_widget import MockExamsWidget
        from src.ui.statistics_widget import StatisticsWidget
        from src.ui.library_widget import LibraryWidget
        from src.ui.goal_widget import GoalWidget

        pages_map = [
            ('Home',       DashboardWidget),
            ('Speaking',   SpeakingWidget),
            ('Progress',   ProgressWidget),
            ('Writing',    WritingWidget),
            ('Vocabulary', VocabularyWidget),
            ('Settings',   SettingsWidget),
            ('Reading',    ReadingWidget),
            ('Listening',  ListeningWidget),
            ('Study DNA',  StudyDNAWidget),
            ('Mock Exams', MockExamsWidget),
            ('Statistics', StatisticsWidget),
            ('Library',    LibraryWidget),
            ('Maqsad',     GoalWidget),
        ]

        for name, WidgetClass in pages_map:
            w = WidgetClass(self.db, self.ai)
            self.pages[name] = w
            self.stack.addWidget(w)

    def _navigate(self, page):
        w = self.pages.get(page)
        if w:
            self.stack.setCurrentWidget(w)
            if hasattr(w, 'refresh'):
                w.refresh()
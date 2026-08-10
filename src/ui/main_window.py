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
        ll.setContentsMargins(20, 24, 20, 16)
        logo = QLabel('IFA MENTOR')
        logo.setStyleSheet(
            'font-size:16px;font-weight:bold;'
            'color:#F1F5F9;border:none;'
        )
        sub = QLabel('AI English Coach')
        sub.setStyleSheet(
            'font-size:10px;color:#3B82F6;border:none;'
        )
        ll.addWidget(logo)
        ll.addWidget(sub)
        layout.addWidget(logo_frame)
        nav_w = QWidget()
        nav_w.setStyleSheet('background:transparent;')
        nav_l = QVBoxLayout(nav_w)
        nav_l.setContentsMargins(0, 12, 0, 12)
        nav_l.setSpacing(2)
        pages = [
            'Home', 'Study DNA', 'Reading',
            'Listening', 'Speaking', 'Writing',
            'Vocabulary', 'Library', 'Mock Exams',
            'Progress', 'Statistics', 'Settings'
        ]
        for page in pages:
            icon = SKILL_ICONS.get(page, 'o')
            btn = QPushButton(f'  {icon}  {page}')
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._style(False))
            btn.clicked.connect(
                lambda chk, p=page: self._nav(p)
            )
            self.nav_buttons[page] = btn
            nav_l.addWidget(btn)
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
        uf.setStyleSheet('border-top:1px solid #1E293B;')
        ul = QHBoxLayout(uf)
        ul.setContentsMargins(16, 12, 16, 12)
        av = QLabel('👤')
        av.setStyleSheet('font-size:22px;border:none;')
        il = QVBoxLayout()
        nl = QLabel(USER_NAME)
        nl.setStyleSheet(
            'font-size:13px;font-weight:bold;'
            'color:#F1F5F9;border:none;'
        )
        lv = QLabel('B1 → B2')
        lv.setStyleSheet(
            'font-size:11px;color:#3B82F6;border:none;'
        )
        il.addWidget(nl)
        il.addWidget(lv)
        il.setSpacing(2)
        ul.addWidget(av)
        ul.addLayout(il)
        layout.addWidget(uf)

    def _style(self, active):
        if active:
            return (
                'QPushButton{'
                'background:#1E3A5F;color:#3B82F6;'
                'border:none;'
                'border-left:3px solid #3B82F6;'
                'border-radius:8px;padding:8px 16px;'
                'text-align:left;font-size:13px;'
                'font-weight:bold;margin:1px 8px;}'
            )
        return (
            'QPushButton{'
            'background:transparent;color:#94A3B8;'
            'border:none;border-radius:8px;'
            'padding:8px 16px;text-align:left;'
            'font-size:13px;margin:1px 8px;}'
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
        from src.ui.placeholder_widget import PlaceholderWidget

        dash = DashboardWidget(self.db, self.ai)
        self.pages['Home'] = dash
        self.stack.addWidget(dash)

        sp = SpeakingWidget(self.db, self.ai)
        self.pages['Speaking'] = sp
        self.stack.addWidget(sp)

        pr = ProgressWidget(self.db, self.ai)
        self.pages['Progress'] = pr
        self.stack.addWidget(pr)

        wr = WritingWidget(self.db, self.ai)
        self.pages['Writing'] = wr
        self.stack.addWidget(wr)

        vb = VocabularyWidget(self.db, self.ai)
        self.pages['Vocabulary'] = vb
        self.stack.addWidget(vb)

        st = SettingsWidget(self.db, self.ai)
        self.pages['Settings'] = st
        self.stack.addWidget(st)

        rd = ReadingWidget(self.db, self.ai)
        self.pages['Reading'] = rd
        self.stack.addWidget(rd)

        ls = ListeningWidget(self.db, self.ai)
        self.pages['Listening'] = ls
        self.stack.addWidget(ls)

        dna = StudyDNAWidget(self.db, self.ai)
        self.pages['Study DNA'] = dna
        self.stack.addWidget(dna)

        mk = MockExamsWidget(self.db, self.ai)
        self.pages['Mock Exams'] = mk
        self.stack.addWidget(mk)

        for page in ['Library', 'Statistics']:
            w = PlaceholderWidget(page)
            self.pages[page] = w
            self.stack.addWidget(w)

    def _navigate(self, page):
        w = self.pages.get(page)
        if w:
            self.stack.setCurrentWidget(w)
            if hasattr(w, 'refresh'):
                w.refresh()
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from src.ui.styles import MAIN_STYLE, SKILL_ICONS
from config.settings import APP_NAME
from src.user_profile import get_profile


class Sidebar(QWidget):
    def __init__(self, on_navigate, profile=None):
        super().__init__()
        self.on_navigate = on_navigate
        self.profile = profile or {}
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
                       "Speaking", "Writing", "Vocabulary",
                       "Tenses"]},
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
        av = QLabel(self.profile.get("name", "I")[:1].upper())
        self.avatar_lbl = av
        av.setStyleSheet(
            'font-size:16px;font-weight:bold;'
            'color:#3B82F6;border:none;'
        )
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av_l.addWidget(av)

        il = QVBoxLayout()
        il.setSpacing(2)
        self.user_name_label = QLabel(
            self.profile.get("name", "User")
        )
        self.user_name_label.setStyleSheet(
            'font-size:14px;font-weight:bold;'
            'color:#F1F5F9;border:none;'
        )
        current = self.profile.get("current_level", "B1")
        target = self.profile.get("target_level", "B2")
        self.user_level_label = QLabel(
            f'{current} → {target}'
        )
        self.user_level_label.setStyleSheet(
            'font-size:11px;color:#3B82F6;border:none;'
        )
        il.addWidget(self.user_name_label)
        il.addWidget(self.user_level_label)

        ul.addWidget(av_frame)
        ul.addLayout(il)
        ul.addStretch()

        self.user_badge = QLabel(current)
        self.user_badge.setStyleSheet(
            'background:#1E3A5F;color:#3B82F6;'
            'border-radius:6px;padding:3px 8px;'
            'font-size:12px;font-weight:bold;border:none;'
        )
        ul.addWidget(self.user_badge)
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

    def update_profile(self, profile):
        self.profile = profile
        name = profile.get("name", "User")
        current = profile.get("current_level", "B1")
        target = profile.get("target_level", "B2")
        self.user_name_label.setText(name)
        self.user_level_label.setText(f"{current} → {target}")
        self.user_badge.setText(current)
        if hasattr(self, "avatar_lbl"):
            self.avatar_lbl.setText(name[:1].upper())

    def activate(self, page):
        self._nav(page)


class MainWindow(QMainWindow):
    def __init__(self, db, ai, profile=None):
        super().__init__()
        self.db = db
        self.ai = ai
        self.profile = profile or get_profile(db)
        self.pages = {}
        self.pending_daily_task = None
        self.pending_mock_task = None
        self.mock_exam_session = None
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
        self.sidebar = Sidebar(
            self._navigate,
            profile=self.profile,
        )
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
        from src.ui.tenses_widget import TensesWidget

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
            ('Tenses',     TensesWidget),
        ]

        for name, WidgetClass in pages_map:
            if name == "Home":
                w = WidgetClass(
                    self.db,
                    self.ai,
                    on_start_task=self.start_daily_task,
                )
            elif name == "Mock Exams":
                w = WidgetClass(
                    self.db,
                    self.ai,
                    on_start_mock=self.start_mock_exam,
                )
            elif name == "Settings":
                w = WidgetClass(
                    self.db,
                    self.ai,
                    on_profile_saved=self.update_user_display,
                    on_sync_complete=self._on_telegram_sync,
                )
            else:
                w = WidgetClass(self.db, self.ai)

            self._wire_task_callback(w)
            self.pages[name] = w
            self.stack.addWidget(w)

    def _wire_task_callback(self, widget):
        if hasattr(widget, "on_task_completed"):
            widget.on_task_completed = (
                self._on_daily_task_completed
            )
        if hasattr(widget, "on_mock_skill_complete"):
            widget.on_mock_skill_complete = (
                self._on_mock_skill_complete
            )

    def _on_daily_task_completed(self):
        for page_name in (
            "Home",
            "Progress",
            "Statistics",
            "Maqsad",
            "Study DNA",
            "Mock Exams",
            "Settings",
            "Tenses",
        ):
            page = self.pages.get(page_name)
            if page and hasattr(page, "refresh"):
                page.refresh()

    def _on_telegram_sync(self):
        for page_name in ("Library", "Tenses"):
            page = self.pages.get(page_name)
            if page and hasattr(page, "refresh"):
                page.refresh()

    def update_user_display(self):
        self.profile = self.ai.reload_profile(self.db)
        self.sidebar.update_profile(self.profile)

        for page_name in (
            "Home",
            "Progress",
            "Statistics",
            "Maqsad",
            "Study DNA",
            "Mock Exams",
            "Settings",
            "Tenses",
        ):
            page = self.pages.get(page_name)
            if page and hasattr(page, "refresh"):
                page.refresh()

    def start_daily_task(self, task):
        skill_pages = {
            "Speaking": "Speaking",
            "Writing": "Writing",
            "Reading": "Reading",
            "Listening": "Listening",
            "Vocabulary": "Vocabulary",
        }

        page = skill_pages.get(
            task.get("skill", ""),
        )

        if not page:
            return

        self.pending_daily_task = task
        self._navigate(page)

    def start_mock_exam(self, mode, skill=None):
        from PyQt6.QtWidgets import QMessageBox
        from src.mock_exam_session import MockExamSession

        session = MockExamSession(
            self.db,
            mode=mode,
            skill=skill,
        )
        if mode == "full" and not session.is_ready:
            issues = ""
            if session.validation and session.validation.issues:
                issues = "\n\n" + "\n".join(
                    session.validation.issues[:4]
                )
            QMessageBox.warning(
                self,
                "Mock material yo'q",
                "Library da tayyor mock to'plam topilmadi.\n"
                "Avval Telegram kanalidan mock materiallarni "
                "sinxronlang."
                + issues,
            )
            return

        if mode == "single" and not session.is_ready:
            skill_name = (skill or "skill").title()
            issues = ""
            if session.validation and session.validation.issues:
                issues = "\n\n" + "\n".join(
                    session.validation.issues[:4]
                )
            QMessageBox.warning(
                self,
                f"{skill_name} material yo'q",
                f"Tayyor {skill_name} mock to'plami topilmadi."
                + issues,
            )
            return

        self.mock_exam_session = session
        mock_page = self.pages.get("Mock Exams")
        if mock_page:
            mock_page.begin_session(
                session.title,
                skill=session.current_skill() or None,
                step=1,
                total=len(session.skills),
            )
        self._go_to_mock_skill()

    def stop_mock_exam(self):
        self.mock_exam_session = None
        self.pending_mock_task = None
        for page_name in (
            "Listening", "Reading", "Writing", "Speaking",
        ):
            widget = self.pages.get(page_name)
            if not widget:
                continue
            widget.mock_exam_task = None
            if getattr(widget, "_task_banner", None):
                widget._task_banner.hide()
            if page_name == "Listening":
                widget._mock_mode = False
                widget._mock_scores = []
                widget._mock_part_orders = []
                widget._mock_part_index = 0
        mock_page = self.pages.get("Mock Exams")
        if mock_page:
            mock_page.is_running = False
            mock_page.timer.stop()
            mock_page.status_frame.hide()

    def _go_to_mock_skill(self):
        session = self.mock_exam_session
        if not session or session.is_complete():
            self._finish_mock_exam()
            return

        skill = session.current_skill()
        skill_pages = {
            "Listening": "Listening",
            "Reading": "Reading",
            "Writing": "Writing",
            "Speaking": "Speaking",
        }
        page = skill_pages.get(skill)
        if not page:
            session.current_index += 1
            self._go_to_mock_skill()
            return

        self.pending_mock_task = session.build_task()
        self._navigate(page)

    def _on_mock_skill_complete(self, task, score, max_score=75):
        session = self.mock_exam_session
        if not session:
            return

        skill = task.get("skill", session.current_skill())
        session.complete_skill(
            skill,
            score,
            details={"max_score": max_score},
        )
        stored = session.results.get(skill, {})
        display_max = stored.get("max_score", max_score)

        mock_page = self.pages.get("Mock Exams")
        if mock_page:
            mock_page.on_skill_complete(
                skill,
                score,
                display_max,
                session.current_index,
                len(session.skills),
            )

        self._go_to_mock_skill()

    def _finish_mock_exam(self):
        session = self.mock_exam_session
        if not session:
            return

        mock_page = self.pages.get("Mock Exams")
        if mock_page:
            mock_page.show_results(session.results, session.title)

        self.mock_exam_session = None
        self.pending_mock_task = None
        self._navigate("Mock Exams")
        self._on_daily_task_completed()

    def _navigate(self, page):
        w = self.pages.get(page)
        if w:
            self.stack.setCurrentWidget(w)

            if (
                self.pending_mock_task
                and hasattr(w, "apply_mock_exam_task")
            ):
                task = self.pending_mock_task
                self.pending_mock_task = None
                w.apply_mock_exam_task(task)
            elif (
                self.pending_daily_task
                and hasattr(w, "apply_daily_task")
            ):
                task = self.pending_daily_task
                self.pending_daily_task = None
                w.apply_daily_task(task)
            elif hasattr(w, "refresh"):
                w.refresh()
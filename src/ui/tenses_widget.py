import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QProgressBar,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from src.tenses.engine import TensesEngine
from src.tenses.registry import TENSE_ORDER, get_mastery_label


class TenseSignals(QObject):
    mastery_updated = pyqtSignal(dict)


class SectionCard(QFrame):
    def __init__(self, title, color="#3B82F6"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
                border-left:3px solid {color};
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 14, 18, 14)
        self.layout.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color:{color};font-size:11px;"
            "font-weight:bold;letter-spacing:1px;border:none;"
        )
        self.layout.addWidget(title_lbl)

    def add(self, widget):
        self.layout.addWidget(widget)


class TensesWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.engine = TensesEngine(db, ai)
        self.current_key = "present_simple"
        self.practice_set = []
        self.practice_index = 0
        self.session_results = []
        self.signals = TenseSignals()
        self._build()
        self._load_tense("present_simple")

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left: tense list ──
        left = QFrame()
        left.setFixedWidth(220)
        left.setStyleSheet(
            "background:#0F172A;border-right:1px solid #1E293B;"
        )
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(12, 16, 12, 16)
        left_l.setSpacing(8)

        title = QLabel("⏱  Tenses")
        title.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#F1F5F9;border:none;"
        )
        left_l.addWidget(title)

        sub = QLabel("12 ta universal zamon")
        sub.setStyleSheet("color:#94A3B8;font-size:11px;border:none;")
        left_l.addWidget(sub)

        self.tense_buttons = {}
        groups = {"Present": [], "Past": [], "Future": []}
        for key in TENSE_ORDER:
            from src.tenses.registry import get_tense
            t = get_tense(key)
            if t:
                groups[t["group"]].append((key, t["name"]))

        for group_name, items in groups.items():
            grp = QLabel(group_name.upper())
            grp.setStyleSheet(
                "color:#475569;font-size:10px;"
                "font-weight:bold;letter-spacing:1px;border:none;"
                "padding-top:8px;"
            )
            left_l.addWidget(grp)
            for key, name in items:
                btn = QPushButton(name)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(self._tense_btn_style(False))
                btn.clicked.connect(
                    lambda chk, k=key: self._load_tense(k)
                )
                self.tense_buttons[key] = btn
                left_l.addWidget(btn)

        left_l.addStretch()
        root.addWidget(left)

        # ── Right: detail ──
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(
            "QScrollArea{border:none;background:#0A0F1E;}"
        )

        self.detail = QWidget()
        self.detail.setStyleSheet("background:#0A0F1E;")
        self.detail_l = QVBoxLayout(self.detail)
        self.detail_l.setContentsMargins(24, 20, 24, 24)
        self.detail_l.setSpacing(14)

        self.header_name = QLabel()
        self.header_name.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;border:none;"
        )
        self.header_uz = QLabel()
        self.header_uz.setStyleSheet(
            "color:#94A3B8;font-size:13px;border:none;"
        )
        self.mastery_bar = QProgressBar()
        self.mastery_bar.setFixedHeight(8)
        self.mastery_bar.setTextVisible(False)
        self.mastery_bar.setStyleSheet("""
            QProgressBar{background:#1E293B;border-radius:4px;border:none;}
            QProgressBar::chunk{background:#10B981;border-radius:4px;}
        """)
        self.mastery_lbl = QLabel()
        self.mastery_lbl.setStyleSheet(
            "color:#10B981;font-size:12px;border:none;"
        )

        self.detail_l.addWidget(self.header_name)
        self.detail_l.addWidget(self.header_uz)
        self.detail_l.addWidget(self.mastery_bar)
        self.detail_l.addWidget(self.mastery_lbl)

        self.sections_container = QVBoxLayout()
        self.sections_container.setSpacing(12)
        self.detail_l.addLayout(self.sections_container)

        # Practice
        practice_card = SectionCard("MASHQ", "#F59E0B")

        self.session_lbl = QLabel("Vazifa 1/3")
        self.session_lbl.setStyleSheet(
            "color:#F59E0B;font-size:12px;font-weight:bold;border:none;"
        )
        practice_card.add(self.session_lbl)

        self.task_type_lbl = QLabel()
        self.task_type_lbl.setStyleSheet(
            "color:#94A3B8;font-size:11px;border:none;"
        )
        practice_card.add(self.task_type_lbl)

        self.practice_q = QLabel()
        self.practice_q.setWordWrap(True)
        self.practice_q.setStyleSheet(
            "color:#F1F5F9;font-size:13px;border:none;"
        )
        practice_card.add(self.practice_q)

        self.practice_input = QLineEdit()
        self.practice_input.setPlaceholderText("Javobingiz...")
        self.practice_input.setStyleSheet(
            "background:#0F172A;color:#F1F5F9;"
            "border:1px solid #1E293B;border-radius:8px;"
            "padding:8px;font-size:13px;"
        )
        practice_card.add(self.practice_input)

        check_row = QHBoxLayout()
        self.check_btn = QPushButton("✅  Tekshirish")
        self.check_btn.setStyleSheet("""
            QPushButton{background:#3B82F6;color:white;
            border:none;border-radius:8px;padding:10px;
            font-weight:bold;}
            QPushButton:hover{background:#2563EB;}
        """)
        self.check_btn.clicked.connect(self._check_practice)
        self.next_btn = QPushButton("Keyingi →")
        self.next_btn.setStyleSheet("""
            QPushButton{background:#10B981;color:white;
            border:none;border-radius:8px;padding:10px;
            font-weight:bold;}
            QPushButton:hover{background:#059669;}
        """)
        self.next_btn.clicked.connect(self._next_practice)
        self.next_btn.hide()

        self.new_session_btn = QPushButton("🔄  Yangi mashq")
        self.new_session_btn.setStyleSheet("""
            QPushButton{background:#8B5CF6;color:white;
            border:none;border-radius:8px;padding:10px;
            font-weight:bold;}
            QPushButton:hover{background:#7C3AED;}
        """)
        self.new_session_btn.clicked.connect(self._start_practice_session)
        self.new_session_btn.hide()

        self.practice_fb = QLabel()
        self.practice_fb.setWordWrap(True)
        self.practice_fb.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )
        check_row.addWidget(self.check_btn)
        check_row.addWidget(self.next_btn)
        check_row.addWidget(self.new_session_btn)
        practice_card.layout.addLayout(check_row)
        practice_card.add(self.practice_fb)
        self.detail_l.addWidget(practice_card)

        self.detail_l.addStretch()
        right_scroll.setWidget(self.detail)
        root.addWidget(right_scroll, 1)

    def _tense_btn_style(self, active):
        if active:
            return """
                QPushButton{background:#1E3A5F;color:#3B82F6;
                border:none;border-left:3px solid #3B82F6;
                border-radius:6px;padding:8px 10px;
                text-align:left;font-size:12px;font-weight:bold;}
            """
        return """
            QPushButton{background:transparent;color:#94A3B8;
            border:none;border-radius:6px;padding:8px 10px;
            text-align:left;font-size:12px;}
            QPushButton:hover{background:#1E293B;color:#F1F5F9;}
        """

    def _clear_sections(self):
        while self.sections_container.count():
            item = self.sections_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _load_tense(self, tense_key):
        self.current_key = tense_key
        for key, btn in self.tense_buttons.items():
            btn.setStyleSheet(
                self._tense_btn_style(key == tense_key)
            )

        tense = self.engine.get(tense_key)
        if not tense:
            return

        self.header_name.setText(tense["name"])
        self.header_uz.setText(
            f"{tense['uzbek_name']}  •  {tense['time']}"
        )

        mastery = tense.get("mastery", {})
        pct = mastery.get("mastery_pct", 0)
        self.mastery_bar.setValue(int(pct))
        self.mastery_lbl.setText(
            f"Mastery: {pct}% — {get_mastery_label(pct)}"
        )

        self._clear_sections()

        # Meaning
        card = SectionCard("MA'NO")
        lbl = QLabel(tense["meaning"])
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#CBD5E1;font-size:13px;border:none;")
        card.add(lbl)
        self.sections_container.addWidget(card)

        # Formula
        card = SectionCard("FORMULA", "#8B5CF6")
        for key, label in [
            ("affirmative", "Affirmative"),
            ("negative", "Negative"),
            ("question", "Question"),
            ("wh_question", "WH-Question"),
        ]:
            f = tense["formula"].get(key, "")
            fl = QLabel(f"  {label}:  {f}")
            fl.setStyleSheet(
                "color:#F1F5F9;font-size:13px;font-family:monospace;"
                "background:#0F172A;border-radius:6px;"
                "padding:6px 10px;border:none;"
            )
            card.add(fl)
        self.sections_container.addWidget(card)

        # Auxiliary
        card = SectionCard("YORDAMCHI FE'L", "#10B981")
        aux = tense.get("auxiliary", {})
        al = QLabel(aux.get("rule", ""))
        al.setWordWrap(True)
        al.setStyleSheet("color:#CBD5E1;font-size:12px;border:none;")
        card.add(al)
        self.sections_container.addWidget(card)

        # Pronoun table
        pronouns = tense.get("pronouns", [])
        if pronouns:
            card = SectionCard("OLMOSHLAR")
            grid = QGridLayout()
            grid.addWidget(QLabel("Pronoun"), 0, 0)
            grid.addWidget(QLabel("Aux"), 0, 1)
            grid.addWidget(QLabel("Verb"), 0, 2)
            for i, row in enumerate(pronouns[:7], 1):
                for j, key in enumerate(
                    ["pronoun", "auxiliary", "verb"]
                ):
                    val = row.get(key, "")
                    l = QLabel(str(val))
                    l.setStyleSheet(
                        "color:#94A3B8;font-size:11px;border:none;"
                    )
                    grid.addWidget(l, i, j)
            card.layout.addLayout(grid)
            self.sections_container.addWidget(card)

        # Important rule
        if tense.get("important_rule"):
            card = SectionCard("MUHIM QOIDA", "#F59E0B")
            rl = QLabel(tense["important_rule"])
            rl.setWordWrap(True)
            rl.setStyleSheet("color:#FCD34D;font-size:12px;border:none;")
            card.add(rl)
            self.sections_container.addWidget(card)

        # Usage
        card = SectionCard("QO'LLANILISH")
        for u in tense.get("usage", []):
            ul = QLabel(
                f"• {u['title']}: {u['rule_uz']}\n"
                f"  e.g. {u['examples'][0] if u.get('examples') else ''}"
            )
            ul.setWordWrap(True)
            ul.setStyleSheet(
                "color:#CBD5E1;font-size:12px;border:none;"
                "padding:4px 0;"
            )
            card.add(ul)
        self.sections_container.addWidget(card)

        # Signal words
        card = SectionCard("SIGNAL WORDS", "#C084FC")
        sw = QLabel(", ".join(tense.get("signal_words", [])))
        sw.setWordWrap(True)
        sw.setStyleSheet("color:#CBD5E1;font-size:12px;border:none;")
        card.add(sw)
        note = tense.get("signal_note", "")
        if note:
            nl = QLabel(f"⚠️ {note}")
            nl.setWordWrap(True)
            nl.setStyleSheet("color:#94A3B8;font-size:11px;border:none;")
            card.add(nl)
        self.sections_container.addWidget(card)

        # Common mistakes
        card = SectionCard("XATOLAR", "#EF4444")
        for m in tense.get("common_mistakes", []):
            ml = QLabel(
                f"❌ {m['wrong']}\n✅ {m['correct']}\n"
                f"   → {m['reason_uz']}"
            )
            ml.setWordWrap(True)
            ml.setStyleSheet(
                "color:#CBD5E1;font-size:12px;border:none;"
                "padding:4px 0;"
            )
            card.add(ml)
        self.sections_container.addWidget(card)

        # Comparison
        comp = self.engine.get_comparison(tense_key)
        if comp:
            card = SectionCard(
                f"TAQQOSLASH: {comp['other']}", "#3B82F6"
            )
            for point in comp.get("points", []):
                if isinstance(point, tuple) and len(point) >= 3:
                    pl = QLabel(
                        f"{point[0]}: {point[1]} vs {point[2]}"
                    )
                else:
                    pl = QLabel(str(point))
                pl.setStyleSheet(
                    "color:#CBD5E1;font-size:12px;border:none;"
                )
                card.add(pl)
            self.sections_container.addWidget(card)

        self._start_practice_session()

    def _start_practice_session(self):
        self.practice_set = self.engine.generate_practice_set(
            self.current_key,
            count=3,
        )
        self.practice_index = 0
        self.session_results = []
        self.new_session_btn.hide()
        self.next_btn.hide()
        self.check_btn.show()
        self.check_btn.setEnabled(True)
        self._show_current_practice()

    def _show_current_practice(self):
        total = len(self.practice_set)
        if self.practice_index >= total:
            self._finish_session()
            return

        exercise = self.practice_set[self.practice_index]
        self.current_exercise = exercise

        self.session_lbl.setText(
            f"Vazifa {self.practice_index + 1}/{total}"
        )
        self.task_type_lbl.setText(
            exercise.get("label", "Mashq")
        )
        self.practice_q.setText(
            exercise.get("question", "")
        )
        self.practice_input.clear()
        self.practice_input.setEnabled(True)
        self.practice_fb.setText("")
        self.practice_fb.setStyleSheet(
            "color:#94A3B8;font-size:12px;border:none;"
        )

    def _finish_session(self):
        correct = sum(
            1 for r in self.session_results if r.get("correct")
        )
        total = len(self.session_results)
        self.session_lbl.setText("Mashq tugadi")
        self.task_type_lbl.setText("")
        self.practice_q.setText(
            f"Natija: {correct}/{total} to'g'ri javob"
        )
        self.practice_input.clear()
        self.practice_input.setEnabled(False)
        self.check_btn.hide()
        self.next_btn.hide()
        self.new_session_btn.show()
        self.practice_fb.setText(
            "✅ Ajoyib!" if correct == total
            else "Yana bir mashq qilib ko'ring."
        )
        self.practice_fb.setStyleSheet(
            "color:#10B981;font-size:12px;border:none;"
        )

    def _next_practice(self):
        self.practice_index += 1
        self.next_btn.hide()
        self.check_btn.show()
        self.check_btn.setEnabled(True)
        self._show_current_practice()

    def _check_practice(self):
        if not self.current_exercise:
            return
        answer = self.practice_input.text()
        result = self.engine.check_answer(
            self.current_key,
            self.current_exercise,
            answer,
        )
        level = self.current_exercise.get("level", 1)
        mastery = self.engine.record_practice(
            self.current_key,
            level,
            result,
        )
        self.session_results.append(result)
        self.practice_fb.setText(result.get("feedback", ""))
        color = "#10B981" if result.get("correct") else "#EF4444"
        self.practice_fb.setStyleSheet(
            f"color:{color};font-size:12px;border:none;"
        )
        pct = mastery.get("pct", 0)
        self.mastery_bar.setValue(int(pct))
        self.mastery_lbl.setText(
            f"Mastery: {pct}% — {mastery.get('label', '')}\n"
            f"{mastery.get('feedback', '')}"
        )

        self.check_btn.setEnabled(False)
        self.practice_input.setEnabled(False)

        if self.practice_index + 1 < len(self.practice_set):
            self.next_btn.show()
        else:
            self.practice_index += 1
            self._finish_session()

    def refresh(self):
        self._load_tense(self.current_key)

import math

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QProgressBar,
    QGridLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPolygonF,
    QFont,
)

from src.scores import get_current_scores


# ============================================================
# COLORS
# ============================================================

BG_COLOR = "#0A0F1E"
CARD_COLOR = "#131C31"
INNER_COLOR = "#0F172A"
BORDER_COLOR = "#1E293B"
TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"

SKILL_COLORS = {
    "Reading": "#10B981",
    "Listening": "#8B5CF6",
    "Speaking": "#3B82F6",
    "Writing": "#C084FC",
    "Vocabulary": "#4ADE80",
    "Grammar": "#F59E0B",
}

SKILL_ICONS = {
    "Reading": "📖",
    "Listening": "🎧",
    "Speaking": "🎤",
    "Writing": "✍️",
    "Vocabulary": "📚",
    "Grammar": "🧠",
}


# ============================================================
# HELPERS
# ============================================================

def clamp_score(value):
    """
    Har qanday score qiymatini 0-100 oralig'iga olib keladi.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0

    return max(0, min(100, value))


def score_to_percent(score):
    """
    CURRENT_SCORES 0-75 formatida.
    Radar / progress esa 0-100 formatida ishlaydi.
    """
    try:
        return clamp_score(
            (float(score) / 75.0) * 100.0
        )
    except (TypeError, ValueError):
        return 0


def format_question_type(value):
    """
    multiple_choice -> Multiple Choice
    matching_headings -> Matching Headings
    """
    if not value:
        return "Practice"

    text = str(value).replace("_", " ").strip()

    return text.title()


# ============================================================
# RADAR CHART
# ============================================================

class RadarChart(QWidget):

    def __init__(
        self,
        scores,
        title="",
    ):
        super().__init__()

        self.scores = scores or {}
        self.title = title

        self.setMinimumSize(
            300,
            300,
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    # --------------------------------------------------------
    # SET SCORES
    # --------------------------------------------------------

    def set_scores(self, scores):

        self.scores = scores or {}

        self.update()

    # --------------------------------------------------------
    # PAINT
    # --------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        cx = width / 2
        cy = height / 2

        # Radar uchun joy
        radius = min(
            width,
            height,
        ) / 2 - 55

        if radius <= 20:
            painter.end()
            return

        skills = list(
            self.scores.keys()
        )

        if not skills:
            painter.end()
            return

        count = len(skills)

        angles = [
            math.pi / 2
            - (
                2
                * math.pi
                * index
                / count
            )
            for index in range(count)
        ]

        # ====================================================
        # GRID CIRCLES
        # ====================================================

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        for level in (
            0.25,
            0.50,
            0.75,
            1.00,
        ):

            radius_level = radius * level

            pen = QPen(
                QColor(BORDER_COLOR)
            )

            pen.setWidth(1)

            painter.setPen(pen)

            painter.drawEllipse(
                int(cx - radius_level),
                int(cy - radius_level),
                int(radius_level * 2),
                int(radius_level * 2),
            )

        # ====================================================
        # AXIS LINES
        # ====================================================

        axis_pen = QPen(
            QColor("#25344D")
        )

        axis_pen.setWidth(1)

        painter.setPen(axis_pen)

        for angle in angles:

            x = (
                cx
                + radius
                * math.cos(angle)
            )

            y = (
                cy
                - radius
                * math.sin(angle)
            )

            painter.drawLine(
                int(cx),
                int(cy),
                int(x),
                int(y),
            )

        # ====================================================
        # DATA POLYGON
        # ====================================================

        points = []

        for index, skill in enumerate(skills):

            score = clamp_score(
                self.scores.get(
                    skill,
                    0,
                )
            )

            ratio = score / 100.0

            x = (
                cx
                + radius
                * ratio
                * math.cos(
                    angles[index]
                )
            )

            y = (
                cy
                - radius
                * ratio
                * math.sin(
                    angles[index]
                )
            )

            points.append(
                QPointF(
                    x,
                    y,
                )
            )

        if len(points) >= 3:

            polygon = QPolygonF(
                points
            )

            polygon_pen = QPen(
                QColor("#3B82F6")
            )

            polygon_pen.setWidth(2)

            painter.setPen(
                polygon_pen
            )

            painter.setBrush(
                QColor(
                    59,
                    130,
                    246,
                    45,
                )
            )

            painter.drawPolygon(
                polygon
            )

        # ====================================================
        # DATA POINTS
        # ====================================================

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        for index, skill in enumerate(skills):

            score = clamp_score(
                self.scores.get(
                    skill,
                    0,
                )
            )

            ratio = score / 100.0

            x = (
                cx
                + radius
                * ratio
                * math.cos(
                    angles[index]
                )
            )

            y = (
                cy
                - radius
                * ratio
                * math.sin(
                    angles[index]
                )
            )

            color = SKILL_COLORS.get(
                skill,
                "#3B82F6",
            )

            painter.setBrush(
                QColor(color)
            )

            painter.drawEllipse(
                int(x) - 5,
                int(y) - 5,
                10,
                10,
            )

        # ====================================================
        # LABELS
        # ====================================================

        font = QFont()

        font.setPointSize(8)

        font.setBold(True)

        painter.setFont(font)

        for index, skill in enumerate(skills):

            angle = angles[index]

            label_distance = (
                radius + 30
            )

            lx = (
                cx
                + label_distance
                * math.cos(angle)
            )

            ly = (
                cy
                - label_distance
                * math.sin(angle)
            )

            color = SKILL_COLORS.get(
                skill,
                TEXT_SECONDARY,
            )

            painter.setPen(
                QColor(color)
            )

            # Skill nomi
            painter.drawText(
                int(lx - 55),
                int(ly - 14),
                110,
                18,
                Qt.AlignmentFlag.AlignCenter,
                str(skill),
            )

            # Score
            painter.setPen(
                QColor(TEXT_SECONDARY)
            )

            score = int(
                clamp_score(
                    self.scores.get(
                        skill,
                        0,
                    )
                )
            )

            painter.drawText(
                int(lx - 55),
                int(ly + 3),
                110,
                18,
                Qt.AlignmentFlag.AlignCenter,
                f"{score}%",
            )

        painter.end()


# ============================================================
# DNA BAR
# ============================================================

class DNABar(QFrame):

    def __init__(
        self,
        skill,
        q_type,
        pct,
        attempts,
    ):
        super().__init__()

        self.skill = skill
        self.q_type = q_type
        self.pct = clamp_score(pct)
        self.attempts = attempts

        self.setStyleSheet(
            """
            QFrame {
                background: transparent;
                border: none;
            }
            """
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            3,
            0,
            3,
        )

        layout.setSpacing(5)

        color = SKILL_COLORS.get(
            skill,
            "#3B82F6",
        )

        # ====================================================
        # STATUS
        # ====================================================

        if self.pct >= 80:

            status = "💪 Kuchli"
            status_color = "#10B981"

        elif self.pct >= 60:

            status = "🟡 O'rta"
            status_color = "#F59E0B"

        else:

            status = "⚠️ Zaif"
            status_color = "#EF4444"

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        header.setSpacing(6)

        type_lbl = QLabel(
            format_question_type(
                q_type
            )
        )

        type_lbl.setWordWrap(
            True
        )

        type_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        type_lbl.setStyleSheet(
            """
            QLabel {
                color:#F1F5F9;
                font-size:12px;
                font-weight:bold;
                border:none;
                background:transparent;
            }
            """
        )

        pct_lbl = QLabel(
            f"{int(self.pct)}%"
        )

        pct_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        pct_lbl.setStyleSheet(
            f"""
            QLabel {{
                color:{color};
                font-size:12px;
                font-weight:bold;
                border:none;
                background:transparent;
            }}
            """
        )

        header.addWidget(
            type_lbl,
            1,
        )

        header.addWidget(
            pct_lbl,
            0,
        )

        layout.addLayout(
            header
        )

        # ====================================================
        # PROGRESS
        # ====================================================

        bar = QProgressBar()

        bar.setValue(
            int(self.pct)
        )

        bar.setTextVisible(
            False
        )

        bar.setFixedHeight(
            6
        )

        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background:#1E293B;
                border-radius:3px;
                border:none;
            }}

            QProgressBar::chunk {{
                background:{color};
                border-radius:3px;
            }}
            """
        )

        layout.addWidget(
            bar
        )

        # ====================================================
        # FOOTER
        # ====================================================

        footer = QHBoxLayout()

        status_lbl = QLabel(
            status
        )

        status_lbl.setStyleSheet(
            f"""
            QLabel {{
                color:{status_color};
                font-size:10px;
                border:none;
                background:transparent;
            }}
            """
        )

        attempts_lbl = QLabel(
            f"{attempts} urinish"
        )

        attempts_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        attempts_lbl.setStyleSheet(
            """
            QLabel {
                color:#475569;
                font-size:10px;
                border:none;
                background:transparent;
            }
            """
        )

        footer.addWidget(
            status_lbl
        )

        footer.addStretch()

        footer.addWidget(
            attempts_lbl
        )

        layout.addLayout(
            footer
        )


# ============================================================
# WEAK POINT CARD
# ============================================================

class WeakPointCard(QFrame):

    def __init__(
        self,
        skill,
        q_type,
        pct,
        tip,
    ):
        super().__init__()

        self.setStyleSheet(
            """
            QFrame {
                background:#1C1C2E;
                border-radius:8px;
                border-left:3px solid #EF4444;
                border-top:1px solid #25253A;
                border-right:1px solid #25253A;
                border-bottom:1px solid #25253A;
            }

            QFrame QLabel {
                background:transparent;
                border:none;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            9,
            12,
            9,
        )

        layout.setSpacing(5)

        # Header
        header = QHBoxLayout()

        title = QLabel(
            f"{skill} — "
            f"{format_question_type(q_type)}"
        )

        title.setWordWrap(
            True
        )

        title.setStyleSheet(
            """
            QLabel {
                color:#F1F5F9;
                font-size:12px;
                font-weight:bold;
            }
            """
        )

        percentage = QLabel(
            f"{int(clamp_score(pct))}%"
        )

        percentage.setStyleSheet(
            """
            QLabel {
                color:#EF4444;
                font-size:12px;
                font-weight:bold;
            }
            """
        )

        header.addWidget(
            title,
            1,
        )

        header.addWidget(
            percentage,
            0,
        )

        layout.addLayout(
            header
        )

        # Tip
        tip_lbl = QLabel(
            f"💡 {tip}"
        )

        tip_lbl.setWordWrap(
            True
        )

        tip_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        tip_lbl.setStyleSheet(
            """
            QLabel {
                color:#94A3B8;
                font-size:11px;
            }
            """
        )

        layout.addWidget(
            tip_lbl
        )


# ============================================================
# STUDY DNA
# ============================================================

class StudyDNAWidget(QWidget):

    def __init__(
        self,
        db,
        ai,
    ):
        super().__init__()

        self.db = db
        self.ai = ai

        self.scroll = None
        self.content = None
        self.main_layout = None

        self._build()

    # ========================================================
    # BUILD
    # ========================================================

    def _build(self):

        self.setStyleSheet(
            f"""
            QWidget {{
                color:{TEXT_PRIMARY};
            }}
            """
        )

        # ====================================================
        # SCROLL
        # ====================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background:{BG_COLOR};
                border:none;
            }}

            QScrollBar:vertical {{
                background:{BG_COLOR};
                width:8px;
                margin:0px;
            }}

            QScrollBar::handle:vertical {{
                background:#334155;
                border-radius:4px;
                min-height:40px;
            }}

            QScrollBar::handle:vertical:hover {{
                background:#475569;
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height:0px;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background:transparent;
            }}
            """
        )

        # ====================================================
        # CONTENT
        # ====================================================

        self.content = QWidget()

        self.content.setStyleSheet(
            f"""
            QWidget {{
                background:{BG_COLOR};
            }}
            """
        )

        self.content.setMinimumWidth(
            760
        )

        self.main_layout = QVBoxLayout(
            self.content
        )

        self.main_layout.setContentsMargins(
            28,
            24,
            28,
            32,
        )

        self.main_layout.setSpacing(
            18
        )

        self.scroll.setWidget(
            self.content
        )

        root = QVBoxLayout(self)

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.addWidget(
            self.scroll
        )

        self._populate()

    # ========================================================
    # CLEAR CONTENT
    # ========================================================

    def _clear_layout(self):

        if self.main_layout is None:
            return

        while self.main_layout.count():

            item = self.main_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

            else:

                child_layout = (
                    item.layout()
                )

                if child_layout:

                    while child_layout.count():

                        child = (
                            child_layout.takeAt(
                                0
                            )
                        )

                        child_widget = (
                            child.widget()
                        )

                        if child_widget:

                            child_widget.deleteLater()

    # ========================================================
    # POPULATE
    # ========================================================

    def _populate(self):

        self._clear_layout()

        # ====================================================
        # HEADER
        # ====================================================

        title = QLabel(
            "🧬  Study DNA"
        )

        title.setStyleSheet(
            """
            QLabel {
                color:#F1F5F9;
                font-size:22px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
            """
        )

        subtitle = QLabel(
            "Har bir skill va savol turini chuqur tahlil qiling."
        )

        subtitle.setWordWrap(
            True
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color:#94A3B8;
                font-size:13px;
                background:transparent;
                border:none;
            }
            """
        )

        self.main_layout.addWidget(
            title
        )

        self.main_layout.addWidget(
            subtitle
        )

        # ====================================================
        # DATA
        # ====================================================

        scores = self._get_scores()

        weak_points = []

        try:
            weak_points = (
                self.db.get_weak_points(
                    threshold=60
                )
                or []
            )
        except Exception as e:

            print(
                f"Study DNA weak points xato: {e}"
            )

        dna_data = []

        try:
            dna_data = (
                self.db.get_weak_points(
                    threshold=100
                )
                or []
            )
        except Exception as e:

            print(
                f"Study DNA analysis xato: {e}"
            )

        # ====================================================
        # TOP SECTION
        # ====================================================

        top = QHBoxLayout()

        top.setSpacing(
            16
        )

        # Radar
        radar_frame = self._create_card()

        radar_layout = QVBoxLayout(
            radar_frame
        )

        radar_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        radar_layout.setSpacing(
            8
        )

        radar_title = QLabel(
            "SKILL RADAR"
        )

        radar_title.setStyleSheet(
            """
            QLabel {
                color:#3B82F6;
                font-size:11px;
                font-weight:bold;
                letter-spacing:1px;
                background:transparent;
                border:none;
            }
            """
        )

        radar_layout.addWidget(
            radar_title
        )

        radar = RadarChart(
            scores
        )

        radar_layout.addWidget(
            radar,
            1,
        )

        top.addWidget(
            radar_frame,
            1,
        )

        # Weak points
        weak_frame = self._create_card()

        weak_layout = QVBoxLayout(
            weak_frame
        )

        weak_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        weak_layout.setSpacing(
            10
        )

        weak_title = QLabel(
            "ZAIF JOYLAR"
        )

        weak_title.setStyleSheet(
            """
            QLabel {
                color:#EF4444;
                font-size:11px;
                font-weight:bold;
                letter-spacing:1px;
                background:transparent;
                border:none;
            }
            """
        )

        weak_layout.addWidget(
            weak_title
        )

        tip_map = {
            "multiple_choice":
                "Savol kalit so'zlariga e'tibor bering.",
            "true_false":
                "'Not Given' — matnda aytilmagan ma'lumot.",
            "matching_headings":
                "Paragrafning asosiy g'oyasini toping.",
            "gap_filling":
                "Bo'sh joy atrofidagi so'zlarga e'tibor bering.",
            "inference":
                "Kontekstdan mantiqiy xulosa chiqaring.",
            "sentence_completion":
                "Audio oldidan savolni o'qib oling.",
            "note_completion":
                "Raqamlar, nomlar va asosiy faktlarni kuzating.",
            "Part1":
                "Shaxsiy savollarga qisqa va aniq javob bering.",
            "Part2":
                "WHAT → WHERE → WHO → DETAILS tuzilmasidan foydalaning.",
            "Part3":
                "Fikr → sabab → misol → xulosa tartibida gapiring.",
            "formal_letter":
                "Dear Sir/Madam → Opening → Body → Closing.",
            "argumentative_essay":
                "Introduction → Body → Counterargument → Conclusion.",
        }

        if weak_points:

            for item in weak_points[:6]:

                skill = item.get(
                    "skill",
                    "Unknown",
                )

                q_type = item.get(
                    "question_type",
                    "practice",
                )

                pct = item.get(
                    "percentage",
                    0,
                )

                tip = tip_map.get(
                    q_type,
                    "Ko'proq mashq qiling va xatolarni tahlil qiling.",
                )

                weak_card = WeakPointCard(
                    skill,
                    q_type,
                    pct,
                    tip,
                )

                weak_layout.addWidget(
                    weak_card
                )

        else:

            no_weak = QLabel(
                "✅ Hozircha zaif joylar aniqlanmagan!\n\n"
                "Mashqlarni davom ettiring."
            )

            no_weak.setWordWrap(
                True
            )

            no_weak.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            no_weak.setStyleSheet(
                """
                QLabel {
                    color:#10B981;
                    font-size:13px;
                    background:transparent;
                    border:none;
                }
                """
            )

            weak_layout.addWidget(
                no_weak
            )

        weak_layout.addStretch()

        top.addWidget(
            weak_frame,
            1,
        )

        self.main_layout.addLayout(
            top
        )

        # ====================================================
        # SKILL ANALYSIS
        # ====================================================

        skills_order = [
            "Reading",
            "Listening",
            "Speaking",
            "Writing",
        ]

        for skill in skills_order:

            skill_items = [
                item
                for item in dna_data
                if item.get("skill") == skill
            ]

            if not skill_items:
                continue

            skill_frame = self._create_card()

            skill_layout = QVBoxLayout(
                skill_frame
            )

            skill_layout.setContentsMargins(
                18,
                16,
                18,
                16,
            )

            skill_layout.setSpacing(
                10
            )

            # Header
            header = QHBoxLayout()

            icon = SKILL_ICONS.get(
                skill,
                "📄",
            )

            color = SKILL_COLORS.get(
                skill,
                "#3B82F6",
            )

            skill_title = QLabel(
                f"{icon}  {skill}"
            )

            skill_title.setStyleSheet(
                f"""
                QLabel {{
                    color:{color};
                    font-size:14px;
                    font-weight:bold;
                    background:transparent;
                    border:none;
                }}
                """
            )

            percentages = []

            for item in skill_items:

                try:
                    percentages.append(
                        float(
                            item.get(
                                "percentage",
                                0,
                            )
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            if percentages:

                average = int(
                    sum(percentages)
                    / len(percentages)
                )

            else:

                average = 0

            avg_label = QLabel(
                f"O'rtacha: {average}%"
            )

            avg_label.setStyleSheet(
                f"""
                QLabel {{
                    color:{color};
                    font-size:12px;
                    font-weight:bold;
                    background:transparent;
                    border:none;
                }}
                """
            )

            header.addWidget(
                skill_title
            )

            header.addStretch()

            header.addWidget(
                avg_label
            )

            skill_layout.addLayout(
                header
            )

            # =================================================
            # DNA BARS
            # =================================================

            grid = QGridLayout()

            grid.setHorizontalSpacing(
                18
            )

            grid.setVerticalSpacing(
                8
            )

            for index, item in enumerate(
                skill_items
            ):

                bar = DNABar(
                    skill,
                    item.get(
                        "question_type",
                        "practice",
                    ),
                    item.get(
                        "percentage",
                        0,
                    ),
                    item.get(
                        "total_attempts",
                        0,
                    ),
                )

                row = index // 2
                column = index % 2

                grid.addWidget(
                    bar,
                    row,
                    column,
                )

            skill_layout.addLayout(
                grid
            )

            self.main_layout.addWidget(
                skill_frame
            )

        # ====================================================
        # RECOMMENDATIONS
        # ====================================================

        self._add_recommendations(
            scores
        )

        # Bottom spacing
        self.main_layout.addSpacing(
            10
        )

    # ========================================================
    # CREATE CARD
    # ========================================================

    def _create_card(self):

        frame = QFrame()

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        frame.setStyleSheet(
            f"""
            QFrame {{
                background:{CARD_COLOR};
                border-radius:12px;
                border:1px solid {BORDER_COLOR};
            }}

            QFrame QLabel {{
                background:transparent;
                border:none;
            }}
            """
        )

        return frame

    # ========================================================
    # SCORES
    # ========================================================

    def _get_scores(self):
        scores = get_current_scores(self.db)

        return {
            "Reading": int(
                score_to_percent(
                    scores.get("reading", 0)
                )
            ),
            "Listening": int(
                score_to_percent(
                    scores.get("listening", 0)
                )
            ),
            "Speaking": int(
                score_to_percent(
                    scores.get("speaking", 0)
                )
            ),
            "Writing": int(
                score_to_percent(
                    scores.get("writing", 0)
                )
            ),
        }

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    def _add_recommendations(
        self,
        scores,
    ):

        frame = QFrame()

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        frame.setStyleSheet(
            """
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E3A5F;
            }

            QFrame QLabel {
                background:transparent;
                border:none;
            }
            """
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(
            10
        )

        title = QLabel(
            "💡 TAVSIYALAR"
        )

        title.setStyleSheet(
            """
            QLabel {
                color:#3B82F6;
                font-size:11px;
                font-weight:bold;
                letter-spacing:1px;
            }
            """
        )

        layout.addWidget(
            title
        )

        recommendations = [
            (
                "🎤 Speaking",
                "Har kuni 10 daqiqa Part 2 mashq qiling. "
                "Rasmga qarab kamida 2 daqiqa gapiring.",
                "#3B82F6",
            ),

            (
                "✍️ Writing",
                "Formal letter strukturasini mustahkamlang: "
                "Opening → Body → Closing.",
                "#C084FC",
            ),

            (
                "🎧 Listening",
                "Har kuni qisqa audio tinglang. "
                "Note completion va keywordlarni mashq qiling.",
                "#8B5CF6",
            ),
        ]

        # Eng zaif skillni aniqlash
        weakest = None
        weakest_score = 101

        for skill, score in scores.items():

            numeric_score = clamp_score(
                score
            )

            if numeric_score < weakest_score:

                weakest_score = numeric_score
                weakest = skill

        if weakest:

            weakest_color = SKILL_COLORS.get(
                weakest,
                "#3B82F6",
            )

            recommendations.insert(
                0,
                (
                    f"🎯 {weakest} — asosiy fokus",
                    f"{weakest} hozir sizning eng zaif skill'ingiz. "
                    f"Bugungi mashg'ulotda unga ko'proq vaqt ajrating.",
                    weakest_color,
                ),
            )

        for (
            rec_title,
            description,
            color,
        ) in recommendations:

            item = QFrame()

            item.setStyleSheet(
                f"""
                QFrame {{
                    background:#0F172A;
                    border-radius:8px;
                    border-left:3px solid {color};
                }}

                QFrame QLabel {{
                    background:transparent;
                    border:none;
                }}
                """
            )

            item_layout = QVBoxLayout(
                item
            )

            item_layout.setContentsMargins(
                12,
                10,
                12,
                10,
            )

            item_layout.setSpacing(
                4
            )

            rec_title_lbl = QLabel(
                rec_title
            )

            rec_title_lbl.setStyleSheet(
                f"""
                QLabel {{
                    color:{color};
                    font-size:12px;
                    font-weight:bold;
                }}
                """
            )

            rec_description = QLabel(
                description
            )

            rec_description.setWordWrap(
                True
            )

            rec_description.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred,
            )

            rec_description.setStyleSheet(
                """
                QLabel {
                    color:#94A3B8;
                    font-size:11px;
                    line-height:140%;
                }
                """
            )

            item_layout.addWidget(
                rec_title_lbl
            )

            item_layout.addWidget(
                rec_description
            )

            layout.addWidget(
                item
            )

        self.main_layout.addWidget(
            frame
        )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self):

        """
        Study DNA sahifasini qayta quradi.
        """

        try:

            self._populate()

        except Exception as e:

            print(
                f"Study DNA refresh xato: {e}"
            )
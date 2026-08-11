import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor,
    QPolygonF, QFont
)
from config.settings import CURRENT_SCORES


class RadarChart(QWidget):
    def __init__(self, scores, title=""):
        super().__init__()
        self.scores = scores
        self.title = title
        self.setMinimumSize(320, 320)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2
        radius = min(w, h) // 2 - 40

        skills = list(self.scores.keys())
        n = len(skills)
        angles = [
            math.pi / 2 - 2 * math.pi * i / n
            for i in range(n)
        ]

        # Grid circles
        for level in [0.25, 0.5, 0.75, 1.0]:
            pen = QPen(QColor("#1E293B"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = int(radius * level)
            painter.drawEllipse(
                cx - r, cy - r, r * 2, r * 2
            )

        # Grid lines
        for angle in angles:
            pen = QPen(QColor("#1E293B"))
            pen.setWidth(1)
            painter.setPen(pen)
            x = int(cx + radius * math.cos(angle))
            y = int(cy - radius * math.sin(angle))
            painter.drawLine(cx, cy, x, y)

        # Data polygon
        points = []
        for i, (skill, score) in enumerate(
            self.scores.items()
        ):
            ratio = min(score / 100, 1.0)
            x = cx + radius * ratio * math.cos(angles[i])
            y = cy - radius * ratio * math.sin(angles[i])
            points.append(QPointF(x, y))

        polygon = QPolygonF(points)
        pen = QPen(QColor("#3B82F6"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QColor(59, 130, 246, 50))
        painter.drawPolygon(polygon)

        # Dot colors
        colors = {
            "Reading":    "#10B981",
            "Listening":  "#8B5CF6",
            "Speaking":   "#3B82F6",
            "Writing":    "#C084FC",
            "Vocabulary": "#4ADE80",
            "Grammar":    "#F59E0B"
        }

        # Points
        for i, (skill, score) in enumerate(
            self.scores.items()
        ):
            ratio = min(score / 100, 1.0)
            x = cx + radius * ratio * math.cos(angles[i])
            y = cy - radius * ratio * math.sin(angles[i])
            color = colors.get(skill, "#3B82F6")
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(x) - 5, int(y) - 5, 10, 10
            )

        # Labels
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        for i, (skill, score) in enumerate(
            self.scores.items()
        ):
            angle = angles[i]
            lx = cx + (radius + 20) * math.cos(angle)
            ly = cy - (radius + 20) * math.sin(angle)
            color = colors.get(skill, "#94A3B8")
            painter.setPen(QColor(color))
            painter.drawText(
                int(lx) - 45, int(ly) - 18,
                90, 14,
                Qt.AlignmentFlag.AlignCenter,
                skill
            )
            painter.drawText(
                int(lx) - 45, int(ly) - 4,
                90, 14,
                Qt.AlignmentFlag.AlignCenter,
                f"{score}%"
            )


class DNABar(QFrame):
    def __init__(self, skill, q_type, pct, attempts):
        super().__init__()
        self.setStyleSheet(
            "background:transparent;border:none;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(4)

        colors = {
            "Reading":    "#10B981",
            "Listening":  "#8B5CF6",
            "Speaking":   "#3B82F6",
            "Writing":    "#C084FC",
            "Vocabulary": "#4ADE80"
        }
        color = colors.get(skill, "#3B82F6")

        if pct >= 80:
            status = "💪 Kuchli"
            status_color = "#10B981"
        elif pct >= 60:
            status = "🟡 O'rta"
            status_color = "#F59E0B"
        else:
            status = "⚠️ Zaif"
            status_color = "#EF4444"

        header = QHBoxLayout()
        type_lbl = QLabel(
            q_type.replace("_", " ").title()
        )
        type_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:12px;"
            "font-weight:bold;border:none;"
        )
        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setStyleSheet(
            f"color:{color};font-size:12px;"
            "font-weight:bold;border:none;"
        )
        status_lbl = QLabel(status)
        status_lbl.setStyleSheet(
            f"color:{status_color};font-size:11px;"
            "border:none;"
        )
        att_lbl = QLabel(f"{attempts} urinish")
        att_lbl.setStyleSheet(
            "color:#475569;font-size:10px;border:none;"
        )

        header.addWidget(type_lbl)
        header.addStretch()
        header.addWidget(status_lbl)
        header.addWidget(pct_lbl)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setValue(int(pct))
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background:#1E293B;
                border-radius:3px;border:none;
            }}
            QProgressBar::chunk {{
                background:{color};border-radius:3px;
            }}
        """)
        layout.addWidget(bar)
        layout.addWidget(att_lbl)


class StudyDNAWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
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
        title = QLabel("🧬  Study DNA")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        sub = QLabel(
            "Har bir skill va savol turini chuqur tahlil"
        )
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Radar + Zaif joylar
        top = QHBoxLayout()
        top.setSpacing(16)

        # Radar chart
        radar_frame = QFrame()
        radar_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        radar_l = QVBoxLayout(radar_frame)
        radar_l.setContentsMargins(16, 16, 16, 16)

        radar_title = QLabel("SKILL RADAR")
        radar_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        radar_l.addWidget(radar_title)

        scores = {
            "Reading": int(
                CURRENT_SCORES["reading"] / 75 * 100
            ),
            "Listening": int(
                CURRENT_SCORES["listening"] / 75 * 100
            ),
            "Speaking": int(
                CURRENT_SCORES["speaking"] / 75 * 100
            ),
            "Writing": int(
                CURRENT_SCORES["writing"] / 75 * 100
            ),
            "Vocabulary": 60,
        }
        radar = RadarChart(scores)
        radar_l.addWidget(radar)
        top.addWidget(radar_frame, 1)

        # Zaif joylar
        weak_frame = QFrame()
        weak_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        weak_l = QVBoxLayout(weak_frame)
        weak_l.setContentsMargins(16, 16, 16, 16)
        weak_l.setSpacing(10)

        weak_title = QLabel("ZAIF JOYLAR")
        weak_title.setStyleSheet(
            "color:#EF4444;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        weak_l.addWidget(weak_title)

        weak_points = self.db.get_weak_points(threshold=60)

        tip_map = {
            "multiple_choice":
                "Savol so'zlariga e'tibor bering",
            "true_false":
                "'Not Given' — matнda aytilmagan",
            "matching_headings":
                "Paragraf asosiy g'oyasini toping",
            "gap_filling":
                "Atrofdagi so'zlarga e'tibor bering",
            "inference":
                "Kontekstdan ma'no chiqaring",
            "sentence_completion":
                "Audio oldidan savolni o'qing",
            "note_completion":
                "Raqamlar va nomlarga e'tibor bering",
            "Part1": "Shaxsiy savollar — qisqa javob",
            "Part2": "Rasm tavsifi — WHAT WHERE WHO",
            "Part3": "Argumentli nutq — PRES tuzilmasi",
            "formal_letter":
                "Dear Sir/Madam bilan boshlang",
            "argumentative_essay":
                "Intro → Body → Counter → Conclusion"
        }

        if weak_points:
            for w in weak_points[:6]:
                skill = w["skill"]
                q_type = w["question_type"]
                pct = w["percentage"]

                item = QFrame()
                item.setStyleSheet("""
                    QFrame {
                        background:#1C1C2E;
                        border-radius:8px;
                        border-left:3px solid #EF4444;
                    }
                """)
                item_l = QVBoxLayout(item)
                item_l.setContentsMargins(12, 8, 12, 8)
                item_l.setSpacing(4)

                header = QHBoxLayout()
                skill_lbl = QLabel(f"{skill} — {q_type}")
                skill_lbl.setStyleSheet(
                    "color:#F1F5F9;font-size:12px;"
                    "font-weight:bold;border:none;"
                )
                pct_lbl = QLabel(f"{pct}%")
                pct_lbl.setStyleSheet(
                    "color:#EF4444;font-size:12px;"
                    "font-weight:bold;border:none;"
                )
                header.addWidget(skill_lbl)
                header.addStretch()
                header.addWidget(pct_lbl)
                item_l.addLayout(header)

                tip = tip_map.get(
                    q_type, "Ko'proq mashq qiling"
                )
                tip_lbl = QLabel(f"💡 {tip}")
                tip_lbl.setStyleSheet(
                    "color:#94A3B8;font-size:11px;border:none;"
                )
                tip_lbl.setWordWrap(True)
                item_l.addWidget(tip_lbl)
                weak_l.addWidget(item)
        else:
            no_weak = QLabel(
                "✅ Hozircha zaif joylar aniqlanmagan!\n"
                "Mashqlarni davom ettiring."
            )
            no_weak.setStyleSheet(
                "color:#10B981;font-size:13px;border:none;"
            )
            no_weak.setAlignment(Qt.AlignmentFlag.AlignCenter)
            weak_l.addWidget(no_weak)

        weak_l.addStretch()
        top.addWidget(weak_frame, 1)
        layout.addLayout(top)

        # DNA tahlili
        dna_data = self.db.get_weak_points(threshold=100)

        skills_order = [
            "Reading", "Listening",
            "Speaking", "Writing", "Vocabulary"
        ]

        for skill in skills_order:
            skill_items = [
                d for d in dna_data
                if d["skill"] == skill
            ]
            if not skill_items:
                continue

            skill_frame = QFrame()
            skill_frame.setStyleSheet("""
                QFrame {
                    background:#131C31;
                    border-radius:12px;
                    border:1px solid #1E293B;
                }
            """)
            skill_l = QVBoxLayout(skill_frame)
            skill_l.setContentsMargins(18, 16, 18, 16)
            skill_l.setSpacing(10)

            skill_colors = {
                "Reading":    "#10B981",
                "Listening":  "#8B5CF6",
                "Speaking":   "#3B82F6",
                "Writing":    "#C084FC",
                "Vocabulary": "#4ADE80"
            }
            skill_icons = {
                "Reading":    "📖",
                "Listening":  "🎧",
                "Speaking":   "🎤",
                "Writing":    "✍️",
                "Vocabulary": "📚"
            }
            color = skill_colors.get(skill, "#3B82F6")
            icon = skill_icons.get(skill, "📄")

            skill_header = QHBoxLayout()
            skill_title = QLabel(f"{icon}  {skill}")
            skill_title.setStyleSheet(
                f"color:{color};font-size:14px;"
                "font-weight:bold;"
            )
            avg_pct = int(
                sum(d["percentage"] for d in skill_items)
                / len(skill_items)
            )
            avg_lbl = QLabel(f"O'rtacha: {avg_pct}%")
            avg_lbl.setStyleSheet(
                f"color:{color};font-size:12px;"
            )
            skill_header.addWidget(skill_title)
            skill_header.addStretch()
            skill_header.addWidget(avg_lbl)
            skill_l.addLayout(skill_header)

            grid = QGridLayout()
            grid.setSpacing(8)
            for i, item in enumerate(skill_items):
                bar = DNABar(
                    skill,
                    item["question_type"],
                    item["percentage"],
                    item["total_attempts"]
                )
                grid.addWidget(bar, i // 2, i % 2)
            skill_l.addLayout(grid)
            layout.addWidget(skill_frame)

        # Tavsiyalar
        rec_frame = QFrame()
        rec_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E3A5F;
            }
        """)
        rec_l = QVBoxLayout(rec_frame)
        rec_l.setContentsMargins(18, 16, 18, 16)
        rec_l.setSpacing(10)

        rec_title = QLabel("💡 TAVSIYALAR")
        rec_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        rec_l.addWidget(rec_title)

        recommendations = [
            (
                "🎤 Speaking (46%)",
                "Har kuni 10 daqiqa Part2 mashq qiling. "
                "Rasm ko'rib 2 daqiqa gapiring.",
                "#3B82F6"
            ),
            (
                "✍️ Writing (57%)",
                "Formal letter strukturasini yod oling: "
                "Opening → Body → Closing.",
                "#C084FC"
            ),
            (
                "🎧 Listening (65%)",
                "BBC 6 Minutes English har kuni tinglang. "
                "Note completion mashq qiling.",
                "#8B5CF6"
            ),
        ]

        for title_r, tip, color in recommendations:
            rec_item = QFrame()
            rec_item.setStyleSheet(f"""
                QFrame {{
                    background:#0F172A;
                    border-radius:8px;
                    border-left:3px solid {color};
                }}
            """)
            rec_item_l = QHBoxLayout(rec_item)
            rec_item_l.setContentsMargins(12, 10, 12, 10)

            text_l = QVBoxLayout()
            t_lbl = QLabel(title_r)
            t_lbl.setStyleSheet(
                f"color:{color};font-size:12px;"
                "font-weight:bold;border:none;"
            )
            d_lbl = QLabel(tip)
            d_lbl.setStyleSheet(
                "color:#94A3B8;font-size:11px;border:none;"
            )
            d_lbl.setWordWrap(True)
            text_l.addWidget(t_lbl)
            text_l.addWidget(d_lbl)
            rec_item_l.addLayout(text_l)
            rec_l.addWidget(rec_item)

        layout.addWidget(rec_frame)
        layout.addStretch()

        scroll.setWidget(content)
        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.addWidget(scroll)

    def refresh(self):
        pass
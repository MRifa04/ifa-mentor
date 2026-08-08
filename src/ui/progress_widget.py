from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygonF
from PyQt6.QtCore import QPointF
import math
from config.settings import CURRENT_SCORES, CEFR_LEVELS, USER_NAME

class RadarChart(QWidget):
    """Study DNA Radar Chart"""
    def __init__(self, scores):
        super().__init__()
        self.scores = scores
        self.setMinimumSize(280, 280)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2
        radius = min(w, h) // 2 - 30

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
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

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
        for i, (skill, score) in enumerate(self.scores.items()):
            ratio = score / 100
            x = cx + radius * ratio * math.cos(angles[i])
            y = cy - radius * ratio * math.sin(angles[i])
            points.append(QPointF(x, y))

        polygon = QPolygonF(points)
        pen = QPen(QColor("#3B82F6"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QColor(59, 130, 246, 40))
        painter.drawPolygon(polygon)

        # Points
        for point in points:
            painter.setBrush(QColor("#3B82F6"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(point.x()) - 4,
                int(point.y()) - 4, 8, 8
            )

        # Labels
        colors = {
            "Reading":    "#10B981",
            "Listening":  "#8B5CF6",
            "Speaking":   "#3B82F6",
            "Writing":    "#C084FC",
            "Vocabulary": "#4ADE80"
        }
        for i, skill in enumerate(skills):
            angle = angles[i]
            lx = cx + (radius + 22) * math.cos(angle)
            ly = cy - (radius + 22) * math.sin(angle)
            color = colors.get(skill, "#94A3B8")
            painter.setPen(QColor(color))
            painter.drawText(
                int(lx) - 35, int(ly) - 8, 70, 16,
                Qt.AlignmentFlag.AlignCenter,
                skill
            )


class MiniProgressBar(QFrame):
    def __init__(self, label, current, target, color):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: bold;"
        )
        val_lbl = QLabel(f"{current} / {target}")
        val_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(val_lbl)
        layout.addLayout(header)

        # Bar
        bar = QProgressBar()
        bar.setValue(int((current / 75) * 100))
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: #1E293B;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(bar)

        # B2 marker
        b2_pct = int((51 / 75) * 100)
        marker = QLabel(f"B2 chegarasi: 51/75")
        marker.setStyleSheet("color: #475569; font-size: 10px;")
        layout.addWidget(marker)


class StatCard(QFrame):
    def __init__(self, title, value, subtitle, color):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: #131C31;
                border-radius: 10px;
                border: 1px solid #1E293B;
                border-top: 3px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: bold;"
        )
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color: #F1F5F9; font-size: 12px; font-weight: bold;"
        )
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #475569; font-size: 11px;")

        layout.addWidget(val_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)


class ProgressWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: #0A0F1E; }"
        )

        content = QWidget()
        content.setStyleSheet("background: #0A0F1E;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header
        title = QLabel("📊  Progress & Statistics")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #F1F5F9;"
        )
        sub = QLabel(
            f"{USER_NAME} — B1 → B2 | "
            "So'nggi 30 kunlik natijalar"
        )
        sub.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Stat cards
        overall = CURRENT_SCORES["overall"]
        gap = max(0, CEFR_LEVELS["B2"][0] - overall)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(12)

        cards = [
            ("Overall Ball", overall, "75 dan", "#3B82F6"),
            ("B2 ga qoldi", f"+{gap}", "ball kerak", "#F59E0B"),
            ("Eng kuchli", "Reading", "73%", "#10B981"),
            ("Eng zaif", "Speaking", "46%", "#EF4444"),
        ]
        for i, (title_c, val, sub_c, color) in enumerate(cards):
            card = StatCard(title_c, val, sub_c, color)
            stats_layout.addWidget(card, 0, i)
        layout.addLayout(stats_layout)

        # Skill progress
        skills_frame = QFrame()
        skills_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        skills_layout = QVBoxLayout(skills_frame)
        skills_layout.setContentsMargins(20, 18, 20, 18)
        skills_layout.setSpacing(12)

        skills_title = QLabel("SKILL OVERVIEW")
        skills_title.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )
        skills_layout.addWidget(skills_title)

        skill_data = [
            ("Reading",   CURRENT_SCORES["reading"],   "#10B981"),
            ("Listening", CURRENT_SCORES["listening"], "#8B5CF6"),
            ("Speaking",  CURRENT_SCORES["speaking"],  "#3B82F6"),
            ("Writing",   CURRENT_SCORES["writing"],   "#C084FC"),
        ]
        for skill, score, color in skill_data:
            bar = MiniProgressBar(skill, score, 75, color)
            skills_layout.addWidget(bar)

        layout.addWidget(skills_frame)

        # Radar + B2 info
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)

        # Radar chart
        radar_frame = QFrame()
        radar_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        radar_layout = QVBoxLayout(radar_frame)
        radar_layout.setContentsMargins(16, 16, 16, 16)

        radar_title = QLabel("STUDY DNA")
        radar_title.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )
        radar_layout.addWidget(radar_title)

        radar_scores = {
            "Reading":    int(CURRENT_SCORES["reading"] / 75 * 100),
            "Listening":  int(CURRENT_SCORES["listening"] / 75 * 100),
            "Speaking":   int(CURRENT_SCORES["speaking"] / 75 * 100),
            "Writing":    int(CURRENT_SCORES["writing"] / 75 * 100),
            "Vocabulary": 60,
        }
        radar = RadarChart(radar_scores)
        radar_layout.addWidget(radar)
        bottom_layout.addWidget(radar_frame, 1)

        # B2 yo'l xaritasi
        roadmap_frame = QFrame()
        roadmap_frame.setStyleSheet("""
            QFrame {
                background: #131C31;
                border-radius: 12px;
                border: 1px solid #1E293B;
            }
        """)
        roadmap_layout = QVBoxLayout(roadmap_frame)
        roadmap_layout.setContentsMargins(20, 18, 20, 18)
        roadmap_layout.setSpacing(12)

        road_title = QLabel("B2 YO'L XARITASI")
        road_title.setStyleSheet(
            "color: #3B82F6; font-size: 11px;"
            "font-weight: bold; letter-spacing: 1px;"
        )
        roadmap_layout.addWidget(road_title)

        # Overall progress
        overall_lbl = QLabel(f"Overall: {overall}/75")
        overall_lbl.setStyleSheet(
            "color: #F1F5F9; font-size: 18px; font-weight: bold;"
        )
        roadmap_layout.addWidget(overall_lbl)

        overall_bar = QProgressBar()
        overall_bar.setValue(int(overall / 75 * 100))
        overall_bar.setTextVisible(False)
        overall_bar.setFixedHeight(10)
        overall_bar.setStyleSheet("""
            QProgressBar {
                background: #1E293B;
                border-radius: 5px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #10B981
                );
                border-radius: 5px;
            }
        """)
        roadmap_layout.addWidget(overall_bar)

        # Darajalar
        levels = [
            ("A2", 26, 40,  "#94A3B8"),
            ("B1", 41, 50,  "#F59E0B"),
            ("B2", 51, 64,  "#10B981"),
            ("C1", 65, 75,  "#3B82F6"),
        ]
        for level, min_s, max_s, color in levels:
            row = QHBoxLayout()
            is_current = min_s <= overall <= max_s
            is_target = level == "B2"

            dot = QLabel(
                "●" if is_current else
                "◎" if is_target else "○"
            )
            dot.setFixedWidth(20)
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")

            lbl = QLabel(
                f"{level}  ({min_s}–{max_s})"
                f"{'  ← Siz' if is_current else ''}"
                f"{'  ← Maqsad' if is_target and not is_current else ''}"
            )
            lbl.setStyleSheet(
                f"color: {color if is_current or is_target else '#475569'};"
                f"font-size: 12px;"
                f"{'font-weight: bold;' if is_current else ''}"
            )
            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            roadmap_layout.addLayout(row)

        roadmap_layout.addStretch()

        # Motivatsiya
        mot = QLabel(f"🎯 B2 ga faqat +{gap} ball kerak!")
        mot.setStyleSheet(
            "color: #10B981; font-size: 13px; font-weight: bold;"
        )
        mot.setWordWrap(True)
        roadmap_layout.addWidget(mot)

        bottom_layout.addWidget(roadmap_frame, 1)
        layout.addLayout(bottom_layout)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def refresh(self):
        pass
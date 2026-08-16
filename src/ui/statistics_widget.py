from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen
from config.settings import CEFR_LEVELS, TARGET_LEVEL
from src.user_profile import get_profile
from src.scores import get_current_scores, EXAM_SKILL_DISPLAY
from datetime import datetime, timedelta


class MiniChart(QWidget):
    def __init__(self, data, color="#3B82F6"):
        super().__init__()
        self.data = data
        self.color = color
        self.setFixedHeight(60)
        self.setMinimumWidth(200)

    def paintEvent(self, event):
        if not self.data:
            return
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        w = self.width()
        h = self.height()
        max_val = max(self.data) if self.data else 1
        min_val = min(self.data) if self.data else 0
        range_val = max_val - min_val or 1

        points = []
        n = len(self.data)
        for i, val in enumerate(self.data):
            x = int(i / (n - 1) * w) if n > 1 else w // 2
            y = int(
                h - ((val - min_val) / range_val) * (h - 8) - 4
            )
            points.append((x, y))

        # Line
        pen = QPen(QColor(self.color))
        pen.setWidth(2)
        painter.setPen(pen)
        for i in range(len(points) - 1):
            painter.drawLine(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1]
            )

        # Last point
        if points:
            painter.setBrush(QColor(self.color))
            painter.setPen(Qt.PenStyle.NoPen)
            lx, ly = points[-1]
            painter.drawEllipse(lx - 4, ly - 4, 8, 8)


class StatBigCard(QFrame):
    def __init__(self, title, value, sub,
                 color, icon, trend=None):
        super().__init__()
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
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            "font-size:20px;border:none;"
        )
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color:#94A3B8;font-size:11px;border:none;"
        )
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        if trend:
            trend_lbl = QLabel(trend)
            trend_color = (
                "#10B981" if "+" in trend else "#EF4444"
            )
            trend_lbl.setStyleSheet(
                f"color:{trend_color};font-size:11px;"
                "font-weight:bold;border:none;"
            )
            header.addWidget(trend_lbl)
        layout.addLayout(header)

        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(
            f"color:{color};font-size:28px;"
            "font-weight:bold;border:none;"
        )
        layout.addWidget(val_lbl)

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            "color:#475569;font-size:11px;border:none;"
        )
        layout.addWidget(sub_lbl)


class SkillStatRow(QFrame):
    def __init__(self, skill, current,
                 target, sessions, color):
        super().__init__()
        self.setStyleSheet(
            "background:transparent;border:none;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        header = QHBoxLayout()
        skill_lbl = QLabel(skill)
        skill_lbl.setStyleSheet(
            f"color:{color};font-size:13px;"
            "font-weight:bold;border:none;"
        )
        skill_lbl.setFixedWidth(100)

        score_lbl = QLabel(f"{current}/75")
        score_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:12px;border:none;"
        )

        sess_lbl = QLabel(f"{sessions} sessiya")
        sess_lbl.setStyleSheet(
            "color:#475569;font-size:11px;border:none;"
        )

        pct = int(current / 75 * 100)
        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setStyleSheet(
            f"color:{color};font-size:12px;"
            "font-weight:bold;border:none;"
        )

        header.addWidget(skill_lbl)
        header.addWidget(score_lbl)
        header.addStretch()
        header.addWidget(sess_lbl)
        header.addWidget(pct_lbl)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setValue(pct)
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

        # B2 marker
        b2_pct = int(51 / 75 * 100)
        marker = QLabel(f"B2 chegara: 51/75 ({b2_pct}%)")
        marker.setStyleSheet(
            "color:#334155;font-size:10px;border:none;"
        )
        layout.addWidget(marker)


class StatisticsWidget(QWidget):
    def __init__(self, db, ai):
        super().__init__()
        self.db = db
        self.ai = ai
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self._build()

    def _current_level_label(self, overall):
        for level, bounds in CEFR_LEVELS.items():
            low, high = bounds
            if low <= overall <= high:
                return level
        return "B1"

    def _build(self):
        self.profile = get_profile(self.db)
        target_level = self.profile.get(
            "target_level",
            TARGET_LEVEL,
        )
        user_name = self.profile.get("name", "User")
        current_level = self.profile.get(
            "current_level",
            "B1",
        )

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
        title = QLabel("📈  Statistika")
        title.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#F1F5F9;"
        )
        sub = QLabel(
            f"{user_name} — {current_level} → {target_level} | "
            "To'liq o'qish statistikasi"
        )
        sub.setStyleSheet("color:#94A3B8;font-size:13px;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Ma'lumot olish
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) as total FROM sessions"
        )
        total_sessions = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) as total FROM vocabulary"
        )
        total_words = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(DISTINCT date) as days
            FROM sessions
        """)
        study_days = cursor.fetchone()["days"]

        cursor.execute("""
            SELECT AVG(percentage) as avg
            FROM sessions
        """)
        avg_score = cursor.fetchone()["avg"] or 0

        # Streak
        cursor.execute("""
            SELECT DISTINCT date FROM sessions
            ORDER BY date DESC LIMIT 30
        """)
        dates = [row["date"] for row in cursor.fetchall()]
        streak = self._calc_streak(dates)

        # Skill sessiyalar
        cursor.execute("""
            SELECT skill, COUNT(*) as cnt,
                   AVG(percentage) as avg_pct
            FROM sessions
            GROUP BY skill
        """)
        skill_stats = {
            row["skill"]: {
                "count": row["cnt"],
                "avg": row["avg_pct"] or 0
            }
            for row in cursor.fetchall()
        }

        # Haftalik progress
        week_data = {}
        for i in range(7):
            date = (
                datetime.now() - timedelta(days=6-i)
            ).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT AVG(percentage) as avg
                FROM sessions WHERE date=?
            """, (date,))
            row = cursor.fetchone()
            week_data[date] = row["avg"] or 0

        self.db.close()

        scores = get_current_scores(self.db)

        # ── Katta statistika kartalar ──
        big_grid = QGridLayout()
        big_grid.setSpacing(12)

        overall = scores["overall"]
        gap = max(
            0,
            CEFR_LEVELS.get(target_level, (51, 64))[0] - overall,
        )
        level_label = self._current_level_label(overall)

        big_cards = [
            (
                "Jami Sessiyalar", total_sessions,
                "Barcha mashqlar", "#3B82F6", "📚"
            ),
            (
                "Study Streak", f"{streak} kun",
                "Ketma-ket o'qish", "#F59E0B", "🔥"
            ),
            (
                "Overall Ball", f"{overall}/75",
                f"Hozirgi daraja: {level_label}", "#10B981", "🎯"
            ),
            (
                f"{target_level} ga qoldi", f"+{gap}",
                "ball kerak", "#EF4444", "⚡"
            ),
            (
                "So'zlar bazasi", total_words,
                "Vocabulary", "#8B5CF6", "📖"
            ),
            (
                "O'qish kunlari", study_days,
                "Jami faol kunlar", "#C084FC", "📅"
            ),
        ]

        for i, (t, v, s, c, ic) in enumerate(big_cards):
            card = StatBigCard(t, v, s, c, ic)
            big_grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(big_grid)

        # ── Skill statistikasi ──
        skill_frame = QFrame()
        skill_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        skill_l = QVBoxLayout(skill_frame)
        skill_l.setContentsMargins(20, 18, 20, 18)
        skill_l.setSpacing(14)

        skill_title = QLabel("SKILL TAHLILI")
        skill_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        skill_l.addWidget(skill_title)

        skill_data = [
            (label, scores[key], color)
            for key, label, color in EXAM_SKILL_DISPLAY
        ]

        for skill, score, color in skill_data:
            stats = skill_stats.get(skill, {})
            sessions = stats.get("count", 0)
            row = SkillStatRow(
                skill, score, 51, sessions, color
            )
            skill_l.addWidget(row)

        layout.addWidget(skill_frame)

        # ── Haftalik grafik ──
        week_frame = QFrame()
        week_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        week_l = QVBoxLayout(week_frame)
        week_l.setContentsMargins(20, 18, 20, 18)
        week_l.setSpacing(10)

        week_title = QLabel("HAFTALIK FAOLLIK")
        week_title.setStyleSheet(
            "color:#3B82F6;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        week_l.addWidget(week_title)

        # Kunlar
        days_row = QHBoxLayout()
        day_names = ["Du", "Se", "Ch", "Pa",
                     "Ju", "Sh", "Ya"]
        week_values = list(week_data.values())

        for i, (day, val) in enumerate(
            zip(day_names, week_values)
        ):
            day_col = QVBoxLayout()
            day_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_col.setSpacing(4)

            # Bar
            bar_h = int(val / 100 * 60) if val > 0 else 4
            bar = QFrame()
            bar.setFixedWidth(28)
            bar.setFixedHeight(max(bar_h, 4))
            color = "#3B82F6" if val >= 60 else (
                "#F59E0B" if val > 0 else "#1E293B"
            )
            bar.setStyleSheet(
                f"background:{color};"
                f"border-radius:4px;"
            )

            val_lbl = QLabel(
                f"{int(val)}%" if val > 0 else "—"
            )
            val_lbl.setStyleSheet(
                "color:#475569;font-size:9px;border:none;"
            )
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            day_lbl = QLabel(day)
            day_lbl.setStyleSheet(
                "color:#94A3B8;font-size:10px;border:none;"
            )
            day_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            day_col.addStretch()
            day_col.addWidget(
                bar,
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            day_col.addWidget(val_lbl)
            day_col.addWidget(day_lbl)
            days_row.addLayout(day_col)

        week_l.addLayout(days_row)
        layout.addWidget(week_frame)

        # ── B2 yo'l xaritasi ──
        road_frame = QFrame()
        road_frame.setStyleSheet("""
            QFrame {
                background:#131C31;
                border-radius:12px;
                border:1px solid #1E293B;
            }
        """)
        road_l = QVBoxLayout(road_frame)
        road_l.setContentsMargins(20, 18, 20, 18)
        road_l.setSpacing(12)

        road_title = QLabel(f"{target_level} YO'L XARITASI")
        road_title.setStyleSheet(
            "color:#10B981;font-size:11px;"
            "font-weight:bold;letter-spacing:1px;"
        )
        road_l.addWidget(road_title)

        overall_lbl = QLabel(
            f"Overall: {overall}/75 — "
            f"{target_level} uchun "
            f"{CEFR_LEVELS.get(target_level, (51,))[0]} kerak"
        )
        overall_lbl.setStyleSheet(
            "color:#F1F5F9;font-size:14px;"
            "font-weight:bold;"
        )
        road_l.addWidget(overall_lbl)

        overall_bar = QProgressBar()
        overall_bar.setValue(int(overall / 75 * 100))
        overall_bar.setTextVisible(False)
        overall_bar.setFixedHeight(12)
        overall_bar.setStyleSheet("""
            QProgressBar {
                background:#1E293B;
                border-radius:6px;border:none;
            }
            QProgressBar::chunk {
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #3B82F6,stop:1 #10B981
                );
                border-radius:6px;
            }
        """)
        road_l.addWidget(overall_bar)

        # Milestones
        milestones = [
            ("A2", 26, 40,  "#94A3B8"),
            ("B1", 41, 50,  "#F59E0B"),
            ("B2", 51, 64,  "#10B981"),
            ("C1", 65, 75,  "#3B82F6"),
        ]
        mile_row = QHBoxLayout()
        for level, mn, mx, color in milestones:
            is_cur = mn <= overall <= mx
            is_tgt = level == target_level
            m_frame = QFrame()
            m_frame.setStyleSheet(f"""
                QFrame {{
                    background:{'#0F2A1E' if is_tgt else '#0F172A'};
                    border-radius:8px;
                    border:1px solid {color if is_cur or is_tgt else '#1E293B'};
                }}
            """)
            m_l = QVBoxLayout(m_frame)
            m_l.setContentsMargins(12, 8, 12, 8)
            m_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

            m_lbl = QLabel(level)
            m_lbl.setStyleSheet(
                f"color:{color};font-size:16px;"
                "font-weight:bold;border:none;"
            )
            m_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            r_lbl = QLabel(f"{mn}–{mx}")
            r_lbl.setStyleSheet(
                "color:#475569;font-size:10px;border:none;"
            )
            r_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if is_cur:
                cur_lbl = QLabel("← Siz")
                cur_lbl.setStyleSheet(
                    f"color:{color};font-size:10px;"
                    "border:none;"
                )
                cur_lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                m_l.addWidget(cur_lbl)

            if is_tgt and not is_cur:
                tgt_lbl = QLabel("🎯 Maqsad")
                tgt_lbl.setStyleSheet(
                    f"color:{color};font-size:10px;"
                    "border:none;"
                )
                tgt_lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                m_l.addWidget(tgt_lbl)

            m_l.addWidget(m_lbl)
            m_l.addWidget(r_lbl)
            mile_row.addWidget(m_frame)

        road_l.addLayout(mile_row)

        # ETA
        days_needed = int(gap / 0.5) if gap > 0 else 0
        eta = (
            datetime.now() + timedelta(days=days_needed)
        ).strftime("%d.%m.%Y")
        eta_lbl = QLabel(
            f"🎯 {target_level} ga taxminiy sana: {eta} "
            f"(+{days_needed} kun)"
        )
        eta_lbl.setStyleSheet(
            "color:#10B981;font-size:13px;"
            "font-weight:bold;"
        )
        road_l.addWidget(eta_lbl)
        layout.addWidget(road_frame)
        layout.addStretch()

        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def _calc_streak(self, dates):
        if not dates:
            return 0
        streak = 0
        today = datetime.now().date()
        for i, d in enumerate(dates):
            try:
                date = datetime.strptime(
                    d, "%Y-%m-%d"
                ).date()
                if date == today - timedelta(days=i):
                    streak += 1
                else:
                    break
            except Exception:
                break
        return streak

    def refresh(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._build()
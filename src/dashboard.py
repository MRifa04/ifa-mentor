import os
import json
from datetime import datetime, timedelta
from config.settings import (
    USER_NAME, CURRENT_LEVEL, TARGET_LEVEL,
    CURRENT_SCORES, CEFR_LEVELS, DATABASE_DIR,
    DAILY_STUDY_TIME, APP_NAME, APP_TAGLINE
)

class Dashboard:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai = ai_engine

    # ─── ASOSIY DASHBOARD ───────────────────────────────────

    def get_dashboard_data(self):
        """
        Dashboard uchun barcha ma'lumotlarni yig'ish
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Progress tarixi
        progress_history = self.db.get_progress_history(days=30)
        today_progress = progress_history[0] if progress_history else {}

        # Zaif joylar
        weak_points = self.db.get_weak_points(threshold=60)

        # Kunlik plan
        today_plan = self.db.get_today_plan()

        # Vocabulary statistika
        conn = self.db.connect()
        cursor = conn.cursor()

        # Jami sessiyalar
        cursor.execute("SELECT COUNT(*) as total FROM sessions")
        total_sessions = cursor.fetchone()["total"]

        # Bugungi sessiyalar
        cursor.execute("""
            SELECT skill, AVG(percentage) as avg
            FROM sessions WHERE date=?
            GROUP BY skill
        """, (today,))
        today_sessions = {
            row["skill"]: round(row["avg"], 1)
            for row in cursor.fetchall()
        }

        # Study streak
        cursor.execute("""
            SELECT DISTINCT date FROM sessions
            ORDER BY date DESC
            LIMIT 30
        """)
        dates = [row["date"] for row in cursor.fetchall()]
        streak = self._calculate_streak(dates)

        # Vocabulary stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END) as mastered,
                SUM(CASE WHEN next_review <= ? THEN 1 ELSE 0 END) as due
            FROM vocabulary
        """, (today,))
        vocab_stats = dict(cursor.fetchone())

        # Haftalik progress
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT date, skill, AVG(percentage) as avg
            FROM sessions
            WHERE date >= ?
            GROUP BY date, skill
            ORDER BY date ASC
        """, (week_ago,))
        weekly_data = cursor.fetchall()

        self.db.close()

        # B2 ga qolgan ball
        current_overall = today_progress.get(
            "overall", CURRENT_SCORES["overall"]
        )
        b2_min = CEFR_LEVELS["B2"][0]
        gap_to_b2 = max(0, b2_min - current_overall)

        return {
            "user": {
                "name": USER_NAME,
                "current_level": CURRENT_LEVEL,
                "target_level": TARGET_LEVEL,
                "streak": streak
            },
            "scores": {
                "listening": today_progress.get(
                    "listening", CURRENT_SCORES["listening"]),
                "reading": today_progress.get(
                    "reading", CURRENT_SCORES["reading"]),
                "writing": today_progress.get(
                    "writing", CURRENT_SCORES["writing"]),
                "speaking": today_progress.get(
                    "speaking", CURRENT_SCORES["speaking"]),
                "overall": current_overall
            },
            "targets": {
                "b2_min": b2_min,
                "gap_to_b2": gap_to_b2,
                "b2_reached": current_overall >= b2_min
            },
            "today": {
                "plan": today_plan,
                "sessions": today_sessions,
                "date": today
            },
            "weak_points": weak_points,
            "vocabulary": vocab_stats,
            "stats": {
                "total_sessions": total_sessions,
                "streak": streak
            },
            "progress_history": progress_history[:14],
            "weekly_data": [dict(r) for r in weekly_data]
        }

    # ─── KUNLIK PLAN ────────────────────────────────────────

    def generate_today_plan(self):
        """
        Bugungi o'qish planini AI bilan yaratish
        """
        weak_points = self.db.get_weak_points(threshold=60)
        progress_history = self.db.get_progress_history(days=7)

        print("\n🤖 Kunlik plan tayyorlanmoqda...")
        plan_data = self.ai.generate_daily_plan(
            weak_points=weak_points,
            progress_history=progress_history
        )

        if "error" in plan_data:
            # Fallback plan
            plan_data = self._default_plan()

        tasks = plan_data.get("tasks", [])

        # Bazaga saqlash
        self.db.create_daily_plan([{
            "skill": t["skill"],
            "task_type": t["task_type"],
            "duration": t["duration"],
            "material_id": None
        } for t in tasks])

        print(f"✅ Bugungi plan tayyor: {len(tasks)} ta vazifa")
        print(f"🎯 Asosiy fokus: {plan_data.get('focus_skill', 'Speaking')}")
        print(f"💬 {plan_data.get('motivational_message', '')}")

        return plan_data

    def _default_plan(self):
        """Fallback kunlik plan"""
        return {
            "focus_skill": "Speaking",
            "reason": "Speaking eng zaif ko'rsatkich",
            "tasks": [
                {
                    "order": 1,
                    "skill": "Speaking",
                    "task_type": "practice",
                    "duration": 30,
                    "description": "Part 2 mashq",
                    "priority": "high"
                },
                {
                    "order": 2,
                    "skill": "Writing",
                    "task_type": "essay",
                    "duration": 25,
                    "description": "Formal letter",
                    "priority": "medium"
                },
                {
                    "order": 3,
                    "skill": "Listening",
                    "task_type": "practice",
                    "duration": 20,
                    "description": "Part 3-4 mashq",
                    "priority": "medium"
                },
                {
                    "order": 4,
                    "skill": "Vocabulary",
                    "task_type": "review",
                    "duration": 15,
                    "description": "Spaced repetition",
                    "priority": "low"
                }
            ],
            "motivational_message": "B2 ga faqat +5 ball kerak!"
        }

    # ─── STUDY DNA ──────────────────────────────────────────

    def get_study_dna(self):
        """
        Study DNA — har bir skill va question type bo'yicha
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT skill, question_type, percentage,
                   total_attempts, correct_answers
            FROM study_dna
            ORDER BY skill, percentage ASC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        self.db.close()

        # Skill bo'yicha guruhlash
        dna = {}
        for row in rows:
            skill = row["skill"]
            if skill not in dna:
                dna[skill] = []
            dna[skill].append({
                "type": row["question_type"],
                "percentage": row["percentage"],
                "attempts": row["total_attempts"],
                "status": self._get_dna_status(row["percentage"])
            })

        return dna

    def _get_dna_status(self, percentage):
        if percentage >= 80:
            return "strong"
        elif percentage >= 60:
            return "medium"
        else:
            return "weak"

    # ─── PROGRESS TAHLIL ────────────────────────────────────

    def get_progress_analysis(self):
        """
        30 kunlik progress tahlili
        """
        history = self.db.get_progress_history(days=30)
        if not history:
            return {"message": "Hali progress ma'lumoti yo'q"}

        skills = ["listening", "reading", "writing", "speaking"]
        analysis = {}

        for skill in skills:
            scores = [
                h[skill] for h in history
                if h.get(skill, 0) > 0
            ]
            if scores:
                analysis[skill] = {
                    "current": scores[0],
                    "start": scores[-1],
                    "change": round(scores[0] - scores[-1], 1),
                    "best": max(scores),
                    "trend": "up" if scores[0] > scores[-1] else "down"
                }

        # B2 ga qolgan kun hisoblash
        current_overall = history[0].get(
            "overall", CURRENT_SCORES["overall"]
        ) if history else CURRENT_SCORES["overall"]

        gap = max(0, CEFR_LEVELS["B2"][0] - current_overall)
        avg_daily_gain = 0.5
        days_to_b2 = int(gap / avg_daily_gain) if gap > 0 else 0
        eta = (
            datetime.now() + timedelta(days=days_to_b2)
        ).strftime("%d.%m.%Y")

        return {
            "skills": analysis,
            "overall": {
                "current": current_overall,
                "target": CEFR_LEVELS["B2"][0],
                "gap": gap,
                "days_to_b2": days_to_b2,
                "eta": eta
            }
        }

    # ─── STREAK HISOBLASH ───────────────────────────────────

    def _calculate_streak(self, dates):
        """Ketma-ket o'qish kunlarini hisoblash"""
        if not dates:
            return 0

        streak = 0
        today = datetime.now().date()

        for i, date_str in enumerate(dates):
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                expected = today - timedelta(days=i)
                if date == expected:
                    streak += 1
                else:
                    break
            except:
                break

        return streak

    # ─── TERMINAL DASHBOARD ─────────────────────────────────

    def show_terminal_dashboard(self):
        """Terminal da dashboard ko'rsatish"""
        data = self.get_dashboard_data()
        scores = data["scores"]
        user = data["user"]
        targets = data["targets"]
        vocab = data["vocabulary"]

        print("\n" + "═" * 60)
        print(f"  {APP_NAME}")
        print(f"  {APP_TAGLINE}")
        print("═" * 60)
        print(f"  Xush kelibsiz, {user['name']}! 🎯")
        print(f"  Daraja: {user['current_level']} → {user['target_level']}")
        print(f"  Study Streak: 🔥 {user['streak']} kun")
        print("─" * 60)

        print("\n📊 JORIY BALLAR:")
        skills = [
            ("Listening", scores["listening"], "🎧"),
            ("Reading",   scores["reading"],   "📖"),
            ("Writing",   scores["writing"],   "✍️"),
            ("Speaking",  scores["speaking"],  "🎤")
        ]

        for name, score, icon in skills:
            bar_filled = int(score / 75 * 20)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            print(f"  {icon} {name:10} [{bar}] {score}/75")

        overall = scores["overall"]
        print(f"\n  Umumiy: {overall}/75")

        if targets["b2_reached"]:
            print("  ✅ B2 DARAJASI OLINDI!")
        else:
            print(f"  🎯 B2 ga: +{targets['gap_to_b2']} ball kerak")

        print("\n─" * 60)
        print("📚 VOCABULARY:")
        print(f"  Jami: {vocab.get('total', 0)} ta so'z")
        print(f"  O'zlashtirilgan: {vocab.get('mastered', 0)} ta")
        print(f"  Bugun takrorlash: {vocab.get('due', 0)} ta")

        print("\n─" * 60)
        today_plan = data["today"]["plan"]
        if today_plan:
            print("📅 BUGUNGI PLAN:")
            for task in today_plan:
                status = "✅" if task.get(
                    "is_completed") else "⬜"
                print(f"  {status} {task['skill']:12} "
                      f"{task['duration_minutes']} min "
                      f"— {task['task_type']}")
        else:
            print("📅 Plan hali yaratilmagan")
            print("   'plan' buyrug'ini yozing")

        weak = data["weak_points"]
        if weak:
            print("\n─" * 60)
            print("⚠️  ZAIF JOYLAR:")
            for w in weak[:3]:
                print(f"  {w['skill']:12} {w['question_type']:20} "
                      f"{w['percentage']}%")

        print("\n═" * 60)
        print("  Buyruqlar: plan | speaking | reading |")
        print("  listening | writing | vocab | stats | exit")
        print("═" * 60)

    # ─── HISOBOT ────────────────────────────────────────────

    def generate_weekly_report(self):
        """Haftalik hisobot"""
        analysis = self.get_progress_analysis()
        dna = self.get_study_dna()

        print("\n" + "═" * 60)
        print("📊 HAFTALIK HISOBOT")
        print("═" * 60)

        skills_data = analysis.get("skills", {})
        for skill, data in skills_data.items():
            trend = "📈" if data["trend"] == "up" else "📉"
            change = data["change"]
            sign = "+" if change >= 0 else ""
            print(f"\n{skill.upper()} {trend}")
            print(f"  Hozir: {data['current']} | "
                  f"O'zgarish: {sign}{change}")
            print(f"  Eng yaxshi: {data['best']}")

        overall = analysis.get("overall", {})
        print(f"\n{'─' * 60}")
        print(f"B2 ga: {overall.get('gap', 0)} ball")
        print(f"Taxminiy sana: {overall.get('eta', 'N/A')}")

        print(f"\n{'─' * 60}")
        print("🧬 STUDY DNA:")
        for skill, items in dna.items():
            weak = [i for i in items if i["status"] == "weak"]
            if weak:
                print(f"\n{skill}:")
                for w in weak:
                    print(f"  ❌ {w['type']:25} {w['percentage']}%")

        print("═" * 60)
        return {"analysis": analysis, "dna": dna}


# Test
if __name__ == "__main__":
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    dash = Dashboard(db, ai)
    print("✅ Dashboard tayyor!")
    dash.show_terminal_dashboard()
    dash.generate_today_plan()
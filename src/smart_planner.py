import json
from datetime import datetime, timedelta
from config.settings import (
    CURRENT_SCORES, CEFR_LEVELS, USER_NAME
)


class SmartPlanner:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    # ── MAQSAD HISOBLASH ────────────────────────────────────

    def calculate_goal_plan(
        self, target_level="B2",
        days=60, daily_minutes=90
    ):
        """
        Maqsad va vaqtga asoslangan to'liq o'quv reja
        """
        current_overall = CURRENT_SCORES["overall"]
        target_overall = CEFR_LEVELS[target_level][0]
        gap = max(0, target_overall - current_overall)

        if gap == 0:
            return {
                "message": f"✅ Siz allaqachon {target_level} darajasida!",
                "gap": 0,
                "achieved": True
            }

        # Kunlik kerakli o'sish
        daily_gain_needed = round(gap / days, 3)

        # Skill og'irliklari (zaif skillga ko'proq vaqt)
        skill_weights = self._calculate_weights()

        # Kunlik vaqt taqsimoti
        daily_plan = self._distribute_time(
            daily_minutes, skill_weights
        )

        # Haftalik jadval
        weekly_schedule = self._create_weekly_schedule(
            daily_plan, daily_minutes
        )

        # Taxminiy natija
        projected_scores = self._project_scores(
            days, daily_plan
        )

        # Milestone sanalar
        milestones = self._calculate_milestones(
            current_overall, target_overall, days
        )

        return {
            "user": USER_NAME,
            "current_overall": current_overall,
            "target_level": target_level,
            "target_overall": target_overall,
            "gap": gap,
            "days": days,
            "daily_minutes": daily_minutes,
            "daily_gain_needed": daily_gain_needed,
            "skill_weights": skill_weights,
            "daily_plan": daily_plan,
            "weekly_schedule": weekly_schedule,
            "projected_scores": projected_scores,
            "milestones": milestones,
            "end_date": (
                datetime.now() + timedelta(days=days)
            ).strftime("%d.%m.%Y"),
            "achieved": False
        }

    def _calculate_weights(self):
        """
        Har bir skill uchun og'irlik hisoblash
        Study DNA va hozirgi ballarga asoslanadi
        """
        scores = CURRENT_SCORES
        max_score = 75

        # Zaiflik darajasi (100 - foiz)
        weaknesses = {
            "speaking":  100 - int(scores["speaking"] / max_score * 100),
            "writing":   100 - int(scores["writing"] / max_score * 100),
            "listening": 100 - int(scores["listening"] / max_score * 100),
            "reading":   100 - int(scores["reading"] / max_score * 100),
            "vocabulary": 40  # Default
        }

        # Study DNA dan zaif joylarni olish
        weak_points = self.db.get_weak_points(threshold=70)
        for w in weak_points:
            skill = w["skill"].lower()
            if skill in weaknesses:
                weaknesses[skill] += 10

        # Normalizatsiya (jami 100%)
        total = sum(weaknesses.values())
        weights = {
            k: round(v / total * 100, 1)
            for k, v in weaknesses.items()
        }

        return weights

    def _distribute_time(self, total_minutes, weights):
        """
        Kunlik vaqtni skilllar bo'yicha taqsimlash
        """
        plan = {}
        for skill, weight in weights.items():
            minutes = round(total_minutes * weight / 100)
            minutes = max(5, min(minutes, 40))
            plan[skill] = minutes

        # Jami tuzatish
        current_total = sum(plan.values())
        if current_total != total_minutes:
            diff = total_minutes - current_total
            # Eng zaif skillga qo'shish
            weakest = max(weights, key=weights.get)
            plan[weakest] = max(5, plan[weakest] + diff)

        return plan

    def _create_weekly_schedule(
        self, daily_plan, daily_minutes
    ):
        """
        7 kunlik jadval — har kun biroz farqli
        """
        days = [
            "Dushanba", "Seshanba", "Chorshanba",
            "Payshanba", "Juma", "Shanba", "Yakshanba"
        ]

        # Skill rotatsiyasi
        skill_focus = [
            "speaking",   # Du
            "writing",    # Se
            "listening",  # Ch
            "reading",    # Pa
            "speaking",   # Ju (speaking ikki marta)
            "vocabulary", # Sh (yengil kun)
            "writing",    # Ya
        ]

        schedule = {}
        for i, day in enumerate(days):
            focus = skill_focus[i]
            day_plan = dict(daily_plan)

            # Fokus skillga +10 min qo'shish
            if focus in day_plan:
                day_plan[focus] += 10
                # Boshqa skilldan -10 olish
                others = [
                    s for s in day_plan
                    if s != focus and day_plan[s] > 10
                ]
                if others:
                    day_plan[others[0]] -= 10

            # Shanba — yengil kun (50%)
            if day == "Shanba":
                day_plan = {
                    k: max(5, v // 2)
                    for k, v in day_plan.items()
                }

            schedule[day] = {
                "focus": focus,
                "plan": day_plan,
                "total": sum(day_plan.values())
            }

        return schedule

    def _project_scores(self, days, daily_plan):
        """
        Mashq qilish natijasida taxminiy ballar
        """
        current = dict(CURRENT_SCORES)

        # Har bir skill uchun o'sish koeffitsienti
        growth_rates = {
            "speaking":  0.08,  # Sekin o'sadi
            "writing":   0.10,
            "listening": 0.12,
            "reading":   0.10,
            "vocabulary": 0.05
        }

        projected = {}
        for skill, minutes in daily_plan.items():
            if skill in current:
                rate = growth_rates.get(skill, 0.08)
                # Kunlik o'sish * kunlar * vaqt koeffitsienti
                time_factor = minutes / 30
                growth = days * rate * time_factor
                new_score = min(
                    75,
                    current[skill] + growth
                )
                projected[skill] = round(new_score, 1)

        # Overall hisoblash
        if projected:
            projected["overall"] = round(
                sum(projected.values()) / len(projected), 1
            )

        return projected

    def _calculate_milestones(
        self, current, target, days
    ):
        """
        Oraliq maqsadlar
        """
        gap = target - current
        milestones = []

        checkpoints = [0.25, 0.5, 0.75, 1.0]
        labels = ["25%", "50%", "75%", "100% 🎉"]

        for pct, label in zip(checkpoints, labels):
            score = round(current + gap * pct, 1)
            day = int(days * pct)
            date = (
                datetime.now() + timedelta(days=day)
            ).strftime("%d.%m.%Y")

            milestones.append({
                "label": label,
                "score": score,
                "day": day,
                "date": date,
                "reached": current >= score
            })

        return milestones

    # ── KUNLIK VAZIFA YANGILASH ──────────────────────────────

    def _build_base_tasks(self, goal_plan):
        """Bugungi odatiy vazifalarni goal_plan'dan yaratadi."""
        daily = goal_plan.get("daily_plan", {})
        skill_task_map = {
            "speaking": "practice",
            "writing": "essay",
            "listening": "practice",
            "reading": "practice",
            "vocabulary": "review"
        }

        return [
            {
                "skill": skill.title(),
                "task_type": skill_task_map.get(skill, "practice"),
                "duration": int(minutes),
                "original_duration_minutes": int(minutes),
            }
            for skill, minutes in daily.items()
        ]

    def _calculate_carryover(self, today=None, window_days=5):
        """
        Oldingi bajarilmagan vazifalarni recovery oynasiga taqsimlaydi.

        Masalan: 100 minutlik vazifa 5 kunlik recovery oynasiga tushsa:
        20 + 20 + 20 + 20 + 20 minut.

        Har kuni source task bazada pending bo'lib qoladi; shuning uchun
        keyingi kunlarda uning navbatdagi ulushi ham avtomatik qo'shiladi.
        """
        today = today or datetime.now().date()
        start = today - timedelta(days=7)
        end = today.strftime("%Y-%m-%d")
        pending = self.db.get_pending_plan_tasks(
            start.strftime("%Y-%m-%d"), end
        )

        if not pending:
            return {}

        allocations = {}

        for task in pending:
            source_date = datetime.strptime(
                task["date"], "%Y-%m-%d"
            ).date()
            elapsed = (today - source_date).days

            # Faqat yaqinda qolgan darslar uchun recovery.
            if elapsed < 1 or elapsed > window_days:
                continue

            minutes = int(
                task.get("original_duration_minutes")
                or task.get("duration_minutes")
                or 0
            )
            if minutes <= 0:
                continue

            # 5 kunlik recovery oynasida teng taqsimlaymiz.
            # Qoldiq minutlar birinchi kunlarga bittadan beriladi.
            base = minutes // window_days
            remainder = minutes % window_days
            share = base + (1 if elapsed <= remainder else 0)

            skill = task["skill"].lower()
            allocations[skill] = allocations.get(skill, 0) + share

        return allocations

    def update_daily_tasks(self, goal_plan):
        """
        Bugungi reja hali mavjud bo'lmasa yaratadi.

        Agar oldingi 1-2 kunning vazifalari bajarilmay qolgan bo'lsa,
        ularning yuklamasini keyingi 5 kunlik oynaga bo'lib, bugungi
        vazifalarga faqat bugungi ulushini qo'shadi.
        """
        if not goal_plan or goal_plan.get("achieved"):
            return

        # Bugungi reja allaqachon yaratilgan bo'lsa, uni qayta yozmaymiz.
        if self.db.get_today_plan():
            return self.db.get_today_plan()

        tasks = self._build_base_tasks(goal_plan)
        carry = self._calculate_carryover()

        if carry:
            for task in tasks:
                skill = task["skill"].lower()
                extra = int(carry.get(skill, 0))
                if extra > 0:
                    task["duration"] += extra
                    # Agar foydalanuvchi bugungi yuklamani ham o'tkazib yuborsa,
                    # keyingi recovery aynan bugungi to'liq yuklama bo'yicha bo'ladi.
                    task["original_duration_minutes"] = task["duration"]
                    task["carryover_minutes"] = extra
                    task["carryover_source_date"] = datetime.now().date().isoformat()

            print(
                "♻️ Carry-over: "
                + ", ".join(f"{k} +{v} min" for k, v in carry.items())
            )

        self.db.create_daily_plan(tasks)
        return self.db.get_today_plan()

    # ── PROGRESS TEKSHIRISH ──────────────────────────────────

    def check_progress(self, goal_plan):
        """
        Hozirgi progress vs reja
        """
        if not goal_plan:
            return None

        history = self.db.get_progress_history(days=7)
        if not history:
            return {
                "on_track": True,
                "message": "Hali ma'lumot yo'q"
            }

        latest = history[0]
        current_overall = latest.get(
            "overall", CURRENT_SCORES["overall"]
        )

        days_passed = (
            datetime.now() - datetime.strptime(
                history[-1]["date"], "%Y-%m-%d"
            )
        ).days + 1

        expected_gain = (
            goal_plan["daily_gain_needed"] * days_passed
        )
        actual_gain = (
            current_overall - CURRENT_SCORES["overall"]
        )

        on_track = actual_gain >= expected_gain * 0.8

        return {
            "on_track": on_track,
            "expected_gain": round(expected_gain, 2),
            "actual_gain": round(actual_gain, 2),
            "days_passed": days_passed,
            "message": (
                "✅ Yaxshi ketmoqda!" if on_track
                else "⚠️ Reja orqasida — ko'proq mashq kerak"
            )
        }

    def save_goal(self, goal_plan):
        """
        Maqsadni bazaga saqlash
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        # Goals jadvali yo'q bo'lsa yaratish
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY,
                target_level TEXT,
                target_overall INTEGER,
                days INTEGER,
                daily_minutes INTEGER,
                start_date TEXT,
                end_date TEXT,
                plan_json TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Eski maqsadni o'chirish
        cursor.execute(
            "UPDATE goals SET is_active=0"
        )

        # Yangi maqsad saqlash
        cursor.execute("""
            INSERT INTO goals
            (target_level, target_overall, days,
             daily_minutes, start_date, end_date, plan_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            goal_plan["target_level"],
            goal_plan["target_overall"],
            goal_plan["days"],
            goal_plan["daily_minutes"],
            datetime.now().strftime("%Y-%m-%d"),
            goal_plan["end_date"],
            json.dumps(goal_plan)
        ))
        conn.commit()
        self.db.close()

    def load_goal(self):
        """
        Aktiv maqsadni yuklash
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM goals
                WHERE is_active=1
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            self.db.close()
            if row:
                return json.loads(row["plan_json"])
        except Exception:
            pass
        return None
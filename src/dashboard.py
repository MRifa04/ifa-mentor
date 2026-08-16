"""
Terminal (CLI) dashboard — src/main.py uchun.
GUI versiyasi: src/ui/dashboard_widget.py
"""

from datetime import datetime

from config.settings import (
    USER_NAME,
    CEFR_LEVELS,
    TARGET_LEVEL,
)
from src.scores import get_current_scores
from src.smart_planner import SmartPlanner


class Dashboard:
    """CLI rejimidagi asosiy dashboard."""

    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    def generate_today_plan(self):
        planner = SmartPlanner(self.db, self.ai)
        goal = planner.load_goal()

        if not goal:
            goal = planner.calculate_goal_plan(
                target_level=TARGET_LEVEL,
            )
            planner.save_goal(goal)

        planner.update_daily_tasks(goal)
        plan = self.db.get_today_plan()

        if plan:
            total = sum(
                int(t.get("duration_minutes", 0) or 0)
                for t in plan
            )
            print(
                f"✅ Kunlik reja tayyor: "
                f"{len(plan)} vazifa, {total} daqiqa"
            )
        else:
            print("⚠️ Kunlik reja yaratilmadi")

        return plan

    def show_terminal_dashboard(self):
        scores = get_current_scores(self.db)
        plan = self.db.get_today_plan()
        target_score = CEFR_LEVELS.get(
            TARGET_LEVEL,
            (51, 64),
        )[0]
        gap = max(
            0,
            target_score - scores.get("overall", 0),
        )

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Xayrli tong"
        elif hour < 18:
            greeting = "Xayrli kun"
        else:
            greeting = "Xayrli kech"

        print("\n" + "═" * 52)
        print(f"  {greeting}, {USER_NAME}!")
        print("  IFA MENTOR — Dashboard")
        print("═" * 52)

        print("\n📊 HOZIRGI BALLAR")
        print("─" * 52)
        for skill in (
            "reading",
            "listening",
            "speaking",
            "writing",
        ):
            value = scores.get(skill, 0)
            bar_len = int(value / 75 * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(
                f"  {skill.title():10} "
                f"[{bar}] {value}/75"
            )

        print(
            f"\n  Overall: {scores.get('overall', 0)}/75"
        )
        print(
            f"  {TARGET_LEVEL} ga qoldi: +{gap} ball"
        )

        print("\n📅 BUGUNGI REJA")
        print("─" * 52)

        if not plan:
            print("  Reja yo'q. 'plan' buyrug'i bilan yarating.")
        else:
            total_min = 0
            for index, task in enumerate(plan, 1):
                done = bool(task.get("is_completed"))
                status = "✅" if done else "⬜"
                minutes = int(
                    task.get("duration_minutes", 0) or 0
                )
                total_min += minutes
                print(
                    f"  {index}. {status} "
                    f"{task.get('skill', ''):12} "
                    f"{minutes:3} min — "
                    f"{task.get('task_type', '')}"
                )
            print(f"\n  Jami: {total_min} daqiqa")

        print("═" * 52)

    def get_progress_analysis(self):
        scores = get_current_scores(self.db)
        target_score = CEFR_LEVELS.get(
            TARGET_LEVEL,
            (51, 64),
        )[0]
        overall = scores.get("overall", 0)
        gap = max(0, target_score - overall)

        planner = SmartPlanner(self.db, self.ai)
        goal = planner.load_goal()
        daily_gain = 0.5
        days_left = 60

        if goal:
            daily_gain = goal.get(
                "daily_gain_needed",
                daily_gain,
            )
            days_left = goal.get("days", days_left)

        eta_days = (
            int(gap / daily_gain)
            if daily_gain > 0
            else days_left
        )

        return {
            "overall": {
                "current": overall,
                "target": target_score,
                "gap": gap,
                "eta": f"~{eta_days} kun",
            },
            "scores": scores,
            "goal": goal,
        }

    def generate_weekly_report(self):
        history = self.db.get_progress_history(days=7)
        scores = get_current_scores(self.db)

        print("\n📈 HAFTALIK HISOBOT")
        print("═" * 50)
        print(
            f"Overall: {scores.get('overall', 0)}/75"
        )

        if history:
            print("\nSo'nggi 7 kun:")
            for row in reversed(history):
                print(
                    f"  {row.get('date')}: "
                    f"overall {row.get('overall', 0)}"
                )
        else:
            print("\nHali progress tarixi yo'q.")

        print("═" * 50)

import os
import json
import time
from datetime import datetime
from config.settings import DATABASE_DIR

class WritingModule:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai = ai_engine
        self.writing_dir = os.path.join(DATABASE_DIR, "writing")
        os.makedirs(self.writing_dir, exist_ok=True)

    # ─── YOZISH TOPSHIRIG'I ─────────────────────────────────

    def get_task(self, task_type="formal_letter", level="B2"):
        """
        Yozish topshirig'i generatsiya qilish
        task_type: formal_letter | argumentative_essay
        """
        print(f"\n✍️  Writing topshirig'i generatsiya: {task_type}")
        task = self.ai.generate_writing_prompt(task_type, level)
        if "error" in task:
            # Fallback topshiriqlar
            fallbacks = {
                "formal_letter": {
                    "task_type": "formal_letter",
                    "level": "B2",
                    "topic": "Complaining about a product",
                    "instructions": "Write a formal letter to the customer service manager of a company complaining about a faulty product you purchased recently.",
                    "min_words": 150,
                    "time_minutes": 30,
                    "points_to_cover": [
                        "Explain what product you bought and when",
                        "Describe the problem with the product",
                        "Say what action you want the company to take"
                    ]
                },
                "argumentative_essay": {
                    "task_type": "argumentative_essay",
                    "level": "B2",
                    "topic": "Technology in education",
                    "instructions": "Some people think that technology brings more problems than benefits to education. To what extent do you agree or disagree?",
                    "min_words": 250,
                    "time_minutes": 40,
                    "points_to_cover": [
                        "State your position clearly",
                        "Give at least 2 arguments with examples",
                        "Address the opposing view",
                        "Write a strong conclusion"
                    ]
                }
            }
            task = fallbacks.get(task_type, fallbacks["formal_letter"])
        return task

    # ─── YOZISH SESSIYASI ───────────────────────────────────

    def run_practice_session(self, task_type="formal_letter", callback=None):
        """
        To'liq writing mashq sessiyasi
        """
        print(f"\n✍️  Writing {task_type} sessiyasi boshlandi")

        # Topshiriq olish
        task = self.get_task(task_type)
        start_time = time.time()

        if callback:
            callback("task_ready", {
                "task": task,
                "timer_minutes": task.get("time_minutes", 30)
            })

        print(f"\n📋 Topshiriq: {task['instructions']}")
        print(f"📌 Ko'rib chiqish kerak bo'lgan nuqtalar:")
        for i, point in enumerate(task.get("points_to_cover", []), 1):
            print(f"   {i}. {point}")
        print(f"⏱️  Vaqt: {task.get('time_minutes', 30)} daqiqa")
        print(f"📝 Minimum so'z: {task.get('min_words', 150)}")

        # Foydalanuvchi yozadi
        print("\n💬 Yozing (tugagach 'DONE' yozing):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "DONE":
                break
            lines.append(line)

        user_essay = "\n".join(lines)
        duration = int((time.time() - start_time) / 60)
        word_count = len(user_essay.split())

        print(f"\n📊 So'zlar soni: {word_count}")
        print("🔄 AI baholayapti...")

        if callback:
            callback("evaluating", {
                "word_count": word_count,
                "essay": user_essay
            })

        # AI baholash
        result = self.ai.evaluate_writing(
            task_type=task_type,
            prompt_text=task["instructions"],
            user_essay=user_essay
        )

        if "error" in result:
            print("❌ Baholashda xato")
            return None

        # Natijani ko'rsatish
        self._show_results(result)

        # Saqlash
        session_id = self.db.save_session(
            skill="Writing",
            score=int(result.get("overall", 0) * 20),
            max_score=100,
            duration=duration,
            details={
                "task_type": task_type,
                "task": task,
                "essay": user_essay,
                "result": result
            }
        )

        # Study DNA
        self.db.update_study_dna(
            "Writing", task_type,
            correct=1 if result.get("overall", 0) >= 3.0 else 0,
            total=1
        )

        # Progress
        score_75 = int(result.get("overall", 0) * 15)
        self.db.update_progress("writing", score_75)

        # Esseni fayl sifatida saqlash
        self._save_essay(user_essay, result, task_type)

        final_result = {
            "task_type": task_type,
            "word_count": word_count,
            "duration_minutes": duration,
            "scores": result.get("scores", {}),
            "overall": result.get("overall", 0),
            "cefr_level": result.get("cefr_level", "B1"),
            "strengths": result.get("strengths", []),
            "improvements": result.get("improvements", []),
            "corrected_sentences": result.get("corrected_sentences", []),
            "session_id": session_id
        }

        if callback:
            callback("session_complete", final_result)

        return final_result

    # ─── NATIJANI KO'RSATISH ────────────────────────────────

    def _show_results(self, result):
        print("\n" + "═" * 50)
        print("📊 WRITING NATIJASI")
        print("═" * 50)

        scores = result.get("scores", {})
        for criterion, data in scores.items():
            score = data.get("score", 0)
            feedback = data.get("feedback", "")
            bar = "█" * int(score) + "░" * (5 - int(score))
            print(f"\n{criterion}:")
            print(f"  [{bar}] {score}/5")
            print(f"  {feedback}")

        overall = result.get("overall", 0)
        cefr = result.get("cefr_level", "B1")
        print(f"\n{'─' * 50}")
        print(f"Umumiy ball: {overall}/5 → CEFR: {cefr}")

        print("\n✅ Kuchli tomonlar:")
        for s in result.get("strengths", []):
            print(f"  + {s}")

        print("\n⚠️  Yaxshilash kerak:")
        for i in result.get("improvements", []):
            print(f"  → {i}")

        corrections = result.get("corrected_sentences", [])
        if corrections:
            print("\n🔧 Grammatika tuzatishlar:")
            for c in corrections[:3]:
                print(f"  ❌ {c.get('original', '')}")
                print(f"  ✅ {c.get('corrected', '')}")
                print(f"  💡 {c.get('reason', '')}")

        print("═" * 50)

    # ─── ESSENI SAQLASH ─────────────────────────────────────

    def _save_essay(self, essay, result, task_type):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"essay_{task_type}_{timestamp}.json"
        filepath = os.path.join(self.writing_dir, filename)

        data = {
            "timestamp": timestamp,
            "task_type": task_type,
            "essay": essay,
            "result": result
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Saqlandi: {filename}")

    # ─── MOCK IMTIHON ───────────────────────────────────────

    def run_mock_exam(self, callback=None):
        """
        To'liq writing mock imtihoni
        Task 1: Formal letter (150+ so'z, 30 daqiqa)
        Task 2: Argumentative essay (250+ so'z, 40 daqiqa)
        """
        print("\n🎓 Writing Mock Imtihon boshlandi!")
        results = {}

        # Task 1
        print("\n━━━ TASK 1: Formal Letter ━━━")
        r1 = self.run_practice_session("formal_letter", callback)
        if r1:
            results["Task1"] = r1

        # Task 2
        print("\n━━━ TASK 2: Argumentative Essay ━━━")
        r2 = self.run_practice_session("argumentative_essay", callback)
        if r2:
            results["Task2"] = r2

        # Umumiy natija
        if results:
            scores = [r.get("overall", 0) for r in results.values()]
            overall = sum(scores) / len(scores)
            cefr = self._score_to_cefr(overall)

            print(f"\n🏆 Writing Mock Yakunlandi!")
            print(f"   Task 1: {results.get('Task1', {}).get('overall', 0)}/5")
            print(f"   Task 2: {results.get('Task2', {}).get('overall', 0)}/5")
            print(f"   Umumiy: {round(overall, 2)}/5 → {cefr}")

            return {
                "type": "mock_exam",
                "overall": round(overall, 2),
                "cefr_level": cefr,
                "tasks": results
            }

    # ─── YOZMA TAHLIL ───────────────────────────────────────

    def analyze_past_essays(self):
        """
        O'tgan esseylarni tahlil qilish
        """
        essays = []
        for f in os.listdir(self.writing_dir):
            if f.endswith(".json"):
                with open(os.path.join(self.writing_dir, f),
                          encoding="utf-8") as file:
                    try:
                        data = json.load(file)
                        essays.append(data)
                    except:
                        pass

        if not essays:
            return "Hali hech qanday essay yozilmagan"

        # Statistika
        scores = []
        for e in essays:
            overall = e.get("result", {}).get("overall", 0)
            if overall:
                scores.append(overall)

        if scores:
            avg = sum(scores) / len(scores)
            best = max(scores)
            print(f"\n📊 Essay tahlili:")
            print(f"   Jami essays: {len(essays)}")
            print(f"   O'rtacha ball: {round(avg, 2)}/5")
            print(f"   Eng yaxshi: {best}/5")
            return {
                "total": len(essays),
                "average": round(avg, 2),
                "best": best,
                "essays": essays
            }

    # ─── VOCABULARY TAVSIYA ─────────────────────────────────

    def get_writing_vocabulary(self, topic):
        """
        Mavzu bo'yicha writing uchun so'zlar
        """
        system = """You are a writing vocabulary coach.
Provide useful phrases and vocabulary for CEFR B2 writing. JSON only."""

        prompt = f"""
Topic: {topic}
Provide B2-level vocabulary and phrases for writing about this topic.
JSON format:
{{
  "topic": "{topic}",
  "linking_words": {{
    "addition": ["Furthermore", "In addition", "Moreover"],
    "contrast": ["However", "On the other hand", "Nevertheless"],
    "cause_effect": ["Therefore", "As a result", "Consequently"],
    "conclusion": ["In conclusion", "To summarize", "Overall"]
  }},
  "topic_vocabulary": [
    {{"word": "sustainable", "example": "sustainable development"}}
  ],
  "useful_phrases": [
    "It is widely acknowledged that...",
    "There is no doubt that..."
  ],
  "sentence_starters": [
    "One of the main advantages is...",
    "Critics argue that..."
  ]
}}"""
        result = self.ai._send(system, prompt, max_tokens=1500)
        try:
            return json.loads(result)
        except:
            return {"error": "Parse xatosi"}

    # ─── YORDAMCHI ──────────────────────────────────────────

    def _score_to_cefr(self, score):
        if score >= 4.5:
            return "C1"
        elif score >= 3.5:
            return "B2"
        elif score >= 2.5:
            return "B1"
        elif score >= 1.5:
            return "A2"
        else:
            return "A1"

    def get_writing_stats(self):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_sessions,
                AVG(score) as avg_score,
                MAX(score) as best_score
            FROM sessions
            WHERE skill='Writing'
        """)
        stats = dict(cursor.fetchone())
        self.db.close()
        return stats

    def get_improvement_tips(self):
        weak = self.db.get_weak_points(threshold=60)
        writing_weak = [w for w in weak if w["skill"] == "Writing"]

        tips = []
        for w in writing_weak:
            task = w["question_type"]
            pct = w["percentage"]
            if task == "formal_letter":
                tips.append(
                    f"Formal Letter ({pct}%): "
                    "Dear Sir/Madam bilan boshlang, "
                    "I am writing to... iborasini ishlating"
                )
            elif task == "argumentative_essay":
                tips.append(
                    f"Essay ({pct}%): "
                    "Introduction → Body (2 paragraph) → "
                    "Counter-argument → Conclusion tuzilmasini saqlang"
                )
        return "\n".join(tips) if tips else "✅ Writing yaxshi ketmoqda!"


# Test
if __name__ == "__main__":
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    writing = WritingModule(db, ai)
    print("✅ Writing Module tayyor!")

    # Topshiriq misoli
    task = writing.get_task("formal_letter")
    print(f"\n📋 Topshiriq: {task['instructions']}")

    # Vocabulary misoli
    vocab = writing.get_writing_vocabulary("technology")
    print(f"\n📚 Linking words: {vocab.get('linking_words', {})}")
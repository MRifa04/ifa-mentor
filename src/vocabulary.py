import os
import json
import time
from datetime import datetime, timedelta
from config.settings import DATABASE_DIR

class VocabularyModule:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai = ai_engine
        self.vocab_dir = os.path.join(DATABASE_DIR, "vocabulary")
        os.makedirs(self.vocab_dir, exist_ok=True)

    # ─── SO'Z QO'SHISH ──────────────────────────────────────

    def add_word_manual(self, word, uzbek="", source="manual"):
        """Qo'lda so'z qo'shish"""
        print(f"\n📚 So'z tahlil qilinmoqda: {word}")

        system = """You are a vocabulary expert for CEFR B2 exam.
Analyze the word and return JSON only, no extra text."""

        prompt = f"""
Analyze this word for CEFR B2 learner: "{word}"
JSON format:
{{
  "word": "{word}",
  "uzbek": "o'zbekcha tarjima",
  "pronunciation": "/fəˈnetɪk/",
  "definition": "clear English definition",
  "level": "B2",
  "example_ai": "Natural example sentence using {word}",
  "word_family": ["noun form", "verb form", "adjective form"],
  "synonyms": ["synonym1", "synonym2"],
  "antonyms": ["antonym1"],
  "collocations": ["common phrase with {word}", "another phrase"],
  "exam_tip": "How this word often appears in CEFR exams"
}}"""

        result = self.ai._send(system, prompt, max_tokens=800)
        try:
            data = json.loads(result)
        except:
            data = {
                "word": word,
                "uzbek": uzbek,
                "pronunciation": "",
                "definition": "",
                "level": "B2",
                "example_ai": "",
                "word_family": [],
                "synonyms": [],
                "antonyms": [],
                "collocations": [],
                "exam_tip": ""
            }

        self.db.add_word(
            word=data.get("word", word),
            uzbek=data.get("uzbek", uzbek),
            pronunciation=data.get("pronunciation", ""),
            definition=data.get("definition", ""),
            example_ai=data.get("example_ai", ""),
            example_book=data.get("collocations", [""])[0],
            source=source,
            level=data.get("level", "B2")
        )

        print(f"✅ Qo'shildi: {word} → {data.get('uzbek', '')}")
        return data

    def mine_from_text(self, text, source=""):
        """
        Matndan muhim so'zlarni avtomatik ajratish
        Vocabulary Mining Engine
        """
        print(f"\n⛏️  Vocabulary Mining: {source}")
        result = self.ai.analyze_vocabulary(text, source)

        if "error" in result:
            print("❌ Mining xatosi")
            return []

        words = result.get("words", [])
        added = 0

        for w in words:
            word = w.get("word", "")
            if not word:
                continue

            # Allaqachon bazada bormi tekshirish
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM vocabulary WHERE word=?",
                (word.lower(),)
            )
            existing = cursor.fetchone()
            self.db.close()

            if existing:
                print(f"  ⏭️  Allaqachon bor: {word}")
                continue

            self.db.add_word(
                word=word,
                uzbek=w.get("uzbek", ""),
                pronunciation=w.get("pronunciation", ""),
                definition=w.get("definition", ""),
                example_ai=w.get("ai_example", ""),
                example_book=w.get("example_from_text", ""),
                source=source,
                level=w.get("level", "B2")
            )
            added += 1
            print(f"  ✅ {word} → {w.get('uzbek', '')}")

        print(f"\n📊 Mining natija: {added} ta yangi so'z qo'shildi")
        return words

    # ─── SPACED REPETITION ──────────────────────────────────

    def run_review_session(self, callback=None):
        """
        Kunlik takrorlash sessiyasi (Spaced Repetition)
        """
        words = self.db.get_words_for_review()

        if not words:
            print("✅ Bugun takrorlash kerak emas!")
            if callback:
                callback("no_words", {
                    "message": "Bugun takrorlash kerak emas!"
                })
            return None

        print(f"\n📚 Bugun takrorlash: {len(words)} ta so'z")
        correct_count = 0
        results = []

        for i, word in enumerate(words):
            print(f"\n{'─' * 40}")
            print(f"So'z {i+1}/{len(words)}")

            if callback:
                callback("word_show", {
                    "word": word["word"],
                    "pronunciation": word.get("pronunciation", ""),
                    "definition": word.get("definition", ""),
                    "example": word.get("example_ai", ""),
                    "uzbek": word.get("uzbek", ""),
                    "index": i + 1,
                    "total": len(words)
                })

            # Terminal mode
            print(f"\n🔤 So'z: {word['word']}")
            print(f"📖 Ta'rif: {word.get('definition', '')}")
            print(f"💬 Misol: {word.get('example_ai', '')}")
            input("\n[Enter] bosing...")
            print(f"🇺🇿 O'zbekcha: {word.get('uzbek', '')}")
            print(f"🔊 Talaffuz: {word.get('pronunciation', '')}")

            ans = input("\nBildingizmi? (y/n): ").strip().lower()
            is_correct = ans == "y"

            if is_correct:
                correct_count += 1
                print("✅ Yaxshi!")
            else:
                print("❌ Keyingi safar eslab qoling!")

            # Natijani saqlash
            self.db.update_word_review(word["id"], is_correct)
            results.append({
                "word": word["word"],
                "correct": is_correct
            })

            if callback:
                callback("word_result", {
                    "word": word["word"],
                    "correct": is_correct,
                    "uzbek": word.get("uzbek", ""),
                    "pronunciation": word.get("pronunciation", ""),
                    "correct_count": correct_count,
                    "index": i + 1
                })

        # Sessiya natijasi
        total = len(words)
        pct = round((correct_count / total * 100), 1) if total > 0 else 0

        self.db.save_session(
            skill="Vocabulary",
            score=correct_count,
            max_score=total,
            duration=int(total * 0.5),
            details={"results": results}
        )

        self.db.update_progress("vocabulary", int(pct * 0.75))

        final = {
            "total_words": total,
            "correct": correct_count,
            "percentage": pct,
            "results": results
        }

        print(f"\n📊 Natija: {correct_count}/{total} ({pct}%)")
        if callback:
            callback("session_complete", final)

        return final

    # ─── SO'Z MASHQLARI ─────────────────────────────────────

    def run_exercise(self, word_data, exercise_type="gap_fill",
                     callback=None):
        """
        Bitta so'z uchun mashq
        exercise_type: gap_fill | speaking | writing | matching
        """
        exercise = self.ai.generate_vocabulary_exercise(
            word=word_data["word"],
            uzbek=word_data.get("uzbek", ""),
            example=word_data.get("example_ai", "")
        )

        if "error" in exercise:
            return None

        exercises = exercise.get("exercises", {})

        if exercise_type == "gap_fill":
            sentence = exercises.get("gap_fill", {}).get("sentence", "")
            answer = exercises.get("gap_fill", {}).get("answer", "")
            print(f"\n✍️  Bo'shliqni to'ldiring:")
            print(f"   {sentence}")
            user_ans = input("Javob: ").strip().lower()
            correct = user_ans == answer.lower()
            print(f"{'✅' if correct else '❌'} To'g'ri javob: {answer}")

        elif exercise_type == "speaking":
            prompt = exercises.get("speaking_prompt", "")
            print(f"\n🎤 Gapiring: {prompt}")
            if callback:
                callback("speaking_exercise", {
                    "word": word_data["word"],
                    "prompt": prompt
                })

        elif exercise_type == "writing":
            prompt = exercises.get("writing_prompt", "")
            print(f"\n✍️  Yozing: {prompt}")
            user_text = input("Javob: ").strip()
            if callback:
                callback("writing_exercise", {
                    "word": word_data["word"],
                    "prompt": prompt,
                    "user_text": user_text
                })

        return exercise

    # ─── BUGUNGI SO'ZLAR ────────────────────────────────────

    def get_daily_words(self, count=15):
        """
        Bugungi 15 ta so'z
        Yangi so'zlar + takrorlash kerakliklari
        """
        # Takrorlash kerak bo'lganlar
        review_words = self.db.get_words_for_review()

        # Yangi so'zlar (agar takrorlash 15 ta to'liq bo'lmasa)
        remaining = max(0, count - len(review_words))
        new_words = []

        if remaining > 0:
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vocabulary
                WHERE status='new'
                ORDER BY created_at ASC
                LIMIT ?
            """, (remaining,))
            rows = cursor.fetchall()
            self.db.close()
            new_words = [dict(r) for r in rows]

        all_words = review_words + new_words
        return all_words[:count]

    def get_vocabulary_stats(self):
        """Vocabulary statistikasi"""
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM vocabulary")
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM vocabulary
            GROUP BY status
        """)
        by_status = {row["status"]: row["count"]
                     for row in cursor.fetchall()}

        cursor.execute("""
            SELECT level, COUNT(*) as count
            FROM vocabulary
            GROUP BY level
        """)
        by_level = {row["level"]: row["count"]
                    for row in cursor.fetchall()}

        # Bugun takrorlash kerak
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COUNT(*) as due
            FROM vocabulary
            WHERE next_review <= ? AND status != 'mastered'
        """, (today,))
        due_today = cursor.fetchone()["due"]

        self.db.close()

        return {
            "total_words": total,
            "by_status": by_status,
            "by_level": by_level,
            "due_today": due_today,
            "mastered": by_status.get("mastered", 0),
            "learning": by_status.get("learning", 0),
            "new": by_status.get("new", 0)
        }

    def show_stats(self):
        stats = self.get_vocabulary_stats()
        print("\n📚 VOCABULARY STATISTIKA")
        print("═" * 40)
        print(f"Jami so'zlar:    {stats['total_words']}")
        print(f"Yangi:           {stats['new']}")
        print(f"O'rganilmoqda:   {stats['learning']}")
        print(f"O'zlashtirilgan: {stats['mastered']}")
        print(f"Bugun takrorlash:{stats['due_today']} ta")
        print("─" * 40)
        print("Daraja bo'yicha:")
        for level, count in stats["by_level"].items():
            print(f"  {level}: {count} ta")
        print("═" * 40)
        return stats

    # ─── WORD OF THE DAY ────────────────────────────────────

    def get_word_of_day(self):
        """Kunlik so'z"""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vocabulary
            WHERE status != 'mastered'
            ORDER BY RANDOM()
            LIMIT 1
        """)
        row = cursor.fetchone()
        self.db.close()

        if row:
            return dict(row)

        # Baza bo'sh bo'lsa — AI dan olish
        system = "You are vocabulary teacher. JSON only."
        prompt = """Give one useful B2-level English word.
JSON format:
{
  "word": "innovative",
  "uzbek": "innovatsion",
  "pronunciation": "/ˈɪnəveɪtɪv/",
  "definition": "introducing new ideas or methods",
  "example": "The company is known for its innovative approach.",
  "uzbek_example": "Kompaniya innovatsion yondashuvi bilan mashhur."
}"""
        result = self.ai._send(system, prompt, max_tokens=300)
        try:
            return json.loads(result)
        except:
            return {
                "word": "sustainable",
                "uzbek": "barqaror",
                "pronunciation": "/səˈsteɪnəbl/",
                "definition": "able to continue over a long period",
                "example": "We need sustainable solutions.",
                "uzbek_example": "Bizga barqaror yechimlar kerak."
            }

    # ─── TAVSIYALAR ─────────────────────────────────────────

    def get_improvement_tips(self):
        stats = self.get_vocabulary_stats()
        tips = []

        if stats["due_today"] > 0:
            tips.append(
                f"⚠️  Bugun {stats['due_today']} ta so'z takrorlash kerak!"
            )
        if stats["total_words"] < 50:
            tips.append(
                "📚 Bazada kam so'z bor. "
                "Reading/Listening dan so'z mining qiling"
            )
        if stats["mastered"] == 0:
            tips.append(
                "💪 Hali hech bir so'z o'zlashtirilmagan. "
                "Har kuni takrorlang!"
            )

        mastered_pct = (
            stats["mastered"] / stats["total_words"] * 100
            if stats["total_words"] > 0 else 0
        )
        if mastered_pct > 50:
            tips.append(
                f"🎉 {mastered_pct:.0f}% so'zlar o'zlashtirilgan! "
                "Yangi so'zlar qo'shing"
            )

        return "\n".join(tips) if tips else "✅ Vocabulary jadal rivojlanmoqda!"


# Test
if __name__ == "__main__":
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    vocab = VocabularyModule(db, ai)
    print("✅ Vocabulary Module tayyor!")

    # Word of the day
    word = vocab.get_word_of_day()
    print(f"\n📌 Bugungi so'z: {word.get('word', '')} "
          f"→ {word.get('uzbek', '')}")

    # Statistika
    vocab.show_stats()

    # Tavsiyalar
    print("\n💡", vocab.get_improvement_tips())
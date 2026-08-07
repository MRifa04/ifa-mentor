import os
import json
import time
import pygame
import threading
from datetime import datetime
from config.settings import DATABASE_DIR

class ListeningModule:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai = ai_engine
        self.listening_dir = os.path.join(DATABASE_DIR, "listening")
        os.makedirs(self.listening_dir, exist_ok=True)

        # Audio player
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.current_audio = None

        # Part qoidalari
        self.PARTS = {
            "Part1": {"level": "B1", "questions": 5,
                      "type": "sentence_completion"},
            "Part2": {"level": "B1", "questions": 5,
                      "type": "multiple_choice"},
            "Part3": {"level": "B2", "questions": 6,
                      "type": "matching"},
            "Part4": {"level": "B2", "questions": 6,
                      "type": "note_completion"},
            "Part5": {"level": "C1", "questions": 4,
                      "type": "multiple_choice"},
            "Part6": {"level": "C1", "questions": 4,
                      "type": "summary_completion"}
        }

    # ─── AUDIO PLAYER ───────────────────────────────────────

    def load_audio(self, audio_path):
        """Audio faylni yuklash"""
        try:
            pygame.mixer.music.load(audio_path)
            self.current_audio = audio_path
            duration = self._get_duration(audio_path)
            print(f"✅ Audio yuklandi: {os.path.basename(audio_path)}")
            print(f"⏱️  Davomiyligi: {duration} soniya")
            return duration
        except Exception as e:
            print(f"❌ Audio xatosi: {e}")
            return 0

    def play(self):
        """Audioni ijro etish"""
        try:
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            print("▶️  Ijro etilmoqda...")
        except Exception as e:
            print(f"❌ Ijro xatosi: {e}")

    def pause(self):
        """Audioni to'xtatib turish"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            print("⏸️  Pauza")

    def resume(self):
        """Audioni davom ettirish"""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("▶️  Davom etmoqda...")

    def stop(self):
        """Audioni to'xtatish"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        print("⏹️  To'xtatildi")

    def set_volume(self, volume):
        """Ovoz balandligi (0.0 - 1.0)"""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def get_position(self):
        """Joriy pozitsiya (millisekund)"""
        return pygame.mixer.music.get_pos()

    def is_audio_playing(self):
        return pygame.mixer.music.get_busy()

    def _get_duration(self, audio_path):
        """Audio davomiyligini olish"""
        try:
            sound = pygame.mixer.Sound(audio_path)
            return int(sound.get_length())
        except:
            return 0

    # ─── TRANSCRIPT OLISH ───────────────────────────────────

    def get_transcript(self, audio_path):
        """
        Audio transkriptini olish
        1. Skript fayl mavjud bo'lsa - o'qiydi
        2. Whisper bilan transkripsiya qiladi
        """
        # Skript faylni tekshirish
        script_path = audio_path.replace(".mp3", ".txt").replace(
            ".ogg", ".txt").replace(".wav", ".txt")

        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                transcript = f.read().strip()
            print(f"📄 Skript topildi: {len(transcript)} belgi")
            return transcript

        # Whisper bilan transkripsiya
        try:
            import whisper
            print("🔄 Whisper transkripsiya qilmoqda...")
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language="en")
            transcript = result["text"].strip()

            # Saqlash
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"✅ Transkripsiya tayyor: {len(transcript)} belgi")
            return transcript

        except ImportError:
            print("⚠️  Whisper o'rnatilmagan")
            return self._generate_sample_transcript()
        except Exception as e:
            print(f"❌ Transkripsiya xatosi: {e}")
            return self._generate_sample_transcript()

    # ─── SAVOLLAR GENERATSIYA ───────────────────────────────

    def generate_test_from_audio(self, audio_path, parts=None):
        """
        Audio asosida to'liq test yaratish
        """
        if parts is None:
            parts = list(self.PARTS.keys())

        transcript = self.get_transcript(audio_path)
        if not transcript:
            print("❌ Transcript olinmadi")
            return None

        print(f"\n🎧 Listening testi generatsiya: {len(parts)} part")
        test_data = {
            "audio_path": audio_path,
            "transcript": transcript,
            "parts": {},
            "total_questions": 0,
            "created_at": datetime.now().isoformat()
        }

        for part_name in parts:
            if part_name not in self.PARTS:
                continue

            rule = self.PARTS[part_name]
            level = rule["level"]
            count = rule["questions"]
            q_type = rule["type"]

            print(f"  ⏳ {part_name} ({level}, {q_type})...")

            questions = self.ai.generate_listening_questions(
                transcript=transcript,
                part_name=part_name,
                level=level,
                question_type=q_type,
                count=count
            )

            if "error" not in questions:
                test_data["parts"][part_name] = {
                    "level": level,
                    "question_type": q_type,
                    "questions": questions.get("questions", []),
                    "count": count
                }
                test_data["total_questions"] += count
                print(f"  ✅ {part_name}: {count} savol tayyor")
            else:
                print(f"  ❌ {part_name}: xato")

        return test_data

    # ─── SESSIYA ────────────────────────────────────────────

    def run_practice_session(self, parts=None, callback=None):
        """
        To'liq listening mashq sessiyasi
        """
        print("\n🎧 Listening sessiyasi boshlandi")

        # Material olish
        material = self.db.get_unused_material("listening", "audio")
        if not material:
            print("⚠️  Audio material topilmadi")
            print("💡 Telegram kanaldan audio yuklab oling yoki qo'lda qo'shing")
            audio_path = None
            transcript = self._generate_sample_transcript()
        else:
            audio_path = material.get("file_path", "")
            print(f"🎵 Audio: {material.get('title', 'Unknown')}")

            if callback:
                callback("material_ready", {
                    "title": material.get("title"),
                    "audio_path": audio_path
                })

            transcript = self.get_transcript(audio_path)

        # Test generatsiya
        print("⏳ Savollar tayyorlanmoqda...")
        if callback:
            callback("generating", {
                "message": "Savollar tayyorlanmoqda..."
            })

        # Savollar generatsiya
        if parts is None:
            parts = list(self.PARTS.keys())

        test_data = {"parts": {}, "total_questions": 0}

        for part_name in parts:
            rule = self.PARTS.get(part_name, {})
            level = rule.get("level", "B2")
            count = rule.get("questions", 5)
            q_type = rule.get("type", "multiple_choice")

            questions = self.ai.generate_listening_questions(
                transcript=transcript,
                part_name=part_name,
                level=level,
                question_type=q_type,
                count=count
            )

            if "error" not in questions:
                test_data["parts"][part_name] = {
                    "level": level,
                    "question_type": q_type,
                    "questions": questions.get("questions", []),
                    "count": count
                }
                test_data["total_questions"] += count

        if not test_data["parts"]:
            print("❌ Savollar generatsiya qilinmadi")
            return None

        # Audio ijro + savollar
        start_time = time.time()
        all_results = {}
        total_correct = 0
        total_questions = 0

        for part_name, part_data in test_data["parts"].items():
            print(f"\n━━━ {part_name} ━━━")
            level = part_data["level"]
            q_type = part_data["question_type"]
            questions = part_data["questions"]

            # Audio ijro
            if audio_path and os.path.exists(audio_path):
                print(f"▶️  Audio tinglanmoqda...")
                self.load_audio(audio_path)
                self.play()

                if callback:
                    callback("audio_playing", {
                        "part": part_name,
                        "audio_path": audio_path
                    })

                # Audio tugashini kutish
                while self.is_audio_playing():
                    time.sleep(0.5)
                    if callback:
                        pos = self.get_position()
                        callback("audio_progress", {"position": pos})

                print("✅ Audio tugadi")
                if callback:
                    callback("audio_complete", {"part": part_name})
            else:
                print(f"📄 Transcript ko'rsatilmoqda...")
                print(f"\n{transcript[:500]}...\n")
                if callback:
                    callback("show_transcript", {
                        "part": part_name,
                        "transcript": transcript
                    })
                time.sleep(3)

            # Savollar
            if callback:
                callback("questions_ready", {
                    "part": part_name,
                    "level": level,
                    "question_type": q_type,
                    "questions": questions
                })

            # Javoblar yig'ish (terminal)
            user_answers = {}
            for i, q in enumerate(questions):
                question_text = q.get("question", "")
                options = q.get("options", {})

                print(f"\nSavol {i+1}: {question_text}")
                if options:
                    for opt, val in options.items():
                        print(f"  {opt}) {val}")
                    ans = input("Javob (A/B/C/D): ").strip().upper()
                else:
                    ans = input("Javob: ").strip()

                user_answers[str(i+1)] = ans

            # Baholash
            correct = 0
            feedback = []
            for i, q in enumerate(questions):
                user_ans = user_answers.get(str(i+1), "")
                correct_ans = str(q.get("answer", ""))
                is_correct = user_ans.upper() == correct_ans.upper()
                if is_correct:
                    correct += 1
                feedback.append({
                    "question_id": i+1,
                    "correct": is_correct,
                    "user_answer": user_ans,
                    "correct_answer": correct_ans,
                    "explanation": q.get("explanation", "")
                })

            total = len(questions)
            pct = round((correct/total*100), 1) if total > 0 else 0
            total_correct += correct
            total_questions += total

            all_results[part_name] = {
                "level": level,
                "correct": correct,
                "total": total,
                "percentage": pct,
                "feedback": feedback,
                "question_type": q_type
            }

            print(f"\n✅ {part_name}: {correct}/{total} ({pct}%)")

            # Study DNA
            self.db.update_study_dna(
                "Listening", q_type,
                correct=correct,
                total=total
            )

            if callback:
                callback("part_complete", {
                    "part": part_name,
                    "correct": correct,
                    "total": total,
                    "percentage": pct,
                    "feedback": feedback
                })

        # Yakunlash
        duration = int((time.time() - start_time) / 60)
        overall_pct = round(
            (total_correct/total_questions*100), 1
        ) if total_questions > 0 else 0

        session_id = self.db.save_session(
            skill="Listening",
            score=total_correct,
            max_score=total_questions,
            duration=duration,
            details={
                "parts": all_results,
                "audio": material.get("title") if material else "generated"
            }
        )

        self.db.update_progress("listening", int(overall_pct * 0.75))

        if material and "id" in material:
            self.db.mark_material_used(material["id"])

        final_result = {
            "total_correct": total_correct,
            "total_questions": total_questions,
            "overall_percentage": overall_pct,
            "duration_minutes": duration,
            "parts": all_results,
            "session_id": session_id
        }

        self._show_results(final_result)

        if callback:
            callback("session_complete", final_result)

        return final_result

    # ─── NATIJANI KO'RSATISH ────────────────────────────────

    def _show_results(self, result):
        print("\n" + "═" * 50)
        print("📊 LISTENING NATIJASI")
        print("═" * 50)

        for part_name, data in result["parts"].items():
            correct = data["correct"]
            total = data["total"]
            pct = data["percentage"]
            level = data["level"]
            bar = "█" * correct + "░" * (total - correct)
            print(f"\n{part_name} ({level}): [{bar}] {correct}/{total} ({pct}%)")

            for fb in data.get("feedback", []):
                if not fb.get("correct"):
                    print(f"  ❌ Savol {fb['question_id']}: "
                          f"Siz: {fb['user_answer']} → "
                          f"To'g'ri: {fb['correct_answer']}")
                    if fb.get("explanation"):
                        print(f"     💡 {fb['explanation']}")

        print(f"\n{'─' * 50}")
        print(f"Jami: {result['total_correct']}/"
              f"{result['total_questions']} "
              f"({result['overall_percentage']}%)")
        print("═" * 50)

    # ─── MOCK IMTIHON ───────────────────────────────────────

    def run_mock_exam(self, callback=None):
        """To'liq listening mock imtihoni (barcha 6 part)"""
        print("\n🎓 Listening Mock Imtihon boshlandi!")
        print("⏱️  Vaqt: 40 daqiqa | Savollar: 30 ta")

        result = self.run_practice_session(
            parts=["Part1", "Part2", "Part3",
                   "Part4", "Part5", "Part6"],
            callback=callback
        )

        if result:
            print(f"\n🏆 Mock Yakunlandi!")
            print(f"   Natija: {result['total_correct']}/30")

        return result

    def run_b2_practice(self, callback=None):
        """Faqat B2 partlar (Part3, Part4)"""
        return self.run_practice_session(
            parts=["Part3", "Part4"],
            callback=callback
        )

    def run_weak_parts(self, callback=None):
        """Zaif partlarni mashq qilish"""
        weak = self.db.get_weak_points(threshold=60)
        listening_weak = [w for w in weak
                         if w["skill"] == "Listening"]

        if not listening_weak:
            print("✅ Listening barcha qismlari yaxshi!")
            return None

        type_to_part = {
            "sentence_completion": "Part1",
            "multiple_choice": "Part2",
            "matching": "Part3",
            "note_completion": "Part4",
            "summary_completion": "Part6"
        }

        weak_parts = []
        for w in listening_weak:
            part = type_to_part.get(w["question_type"])
            if part and part not in weak_parts:
                weak_parts.append(part)

        print(f"🎯 Zaif partlar: {', '.join(weak_parts)}")
        return self.run_practice_session(
            parts=weak_parts,
            callback=callback
        )

    # ─── SAMPLE TRANSCRIPT ──────────────────────────────────

    def _generate_sample_transcript(self):
        """Material bo'lmasa AI transcript yaratadi"""
        system = "Generate a B2-level listening transcript. Plain text only."
        prompt = """Write a 300-word conversation or monologue 
        suitable for CEFR B2 listening exam about technology 
        and daily life."""
        return self.ai._send(system, prompt, max_tokens=500)

    # ─── STATISTIKA ─────────────────────────────────────────

    def get_listening_stats(self):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_sessions,
                AVG(percentage) as avg_percentage,
                MAX(percentage) as best
            FROM sessions
            WHERE skill='Listening'
        """)
        stats = dict(cursor.fetchone())
        self.db.close()
        return stats

    def get_improvement_tips(self):
        weak = self.db.get_weak_points(threshold=60)
        listening_weak = [w for w in weak
                         if w["skill"] == "Listening"]
        tip_map = {
            "sentence_completion": "Part1: Savol so'zlariga e'tibor bering, "
                                   "audio oldidan o'qib chiqing",
            "multiple_choice": "Part2: Distraktorlarga aldanmang, "
                               "asosiy g'oyani toping",
            "matching": "Part3: Parafraz qilingan javoblarga tayyoring",
            "note_completion": "Part4: Raqamlar va nomlarga e'tiborli bo'ling",
            "summary_completion": "Part6: Summary ni avval o'qib, "
                                  "keyin audio tinglaing"
        }
        tips = []
        for w in listening_weak:
            tip = tip_map.get(w["question_type"], "")
            if tip:
                tips.append(f"{tip} ({w['percentage']}%)")
        return "\n".join(tips) if tips else "✅ Listening yaxshi ketmoqda!"


# Test
if __name__ == "__main__":
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    listening = ListeningModule(db, ai)
    print("✅ Listening Module tayyor!")
    stats = listening.get_listening_stats()
    print("📊 Statistika:", stats)
    tips = listening.get_improvement_tips()
    print("💡 Tavsiyalar:", tips)
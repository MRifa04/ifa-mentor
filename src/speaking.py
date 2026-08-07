import os
import json
import time
import wave
import threading
import pyaudio
import speech_recognition as sr
from datetime import datetime
from config.settings import DATABASE_DIR

class SpeakingModule:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai = ai_engine
        self.recognizer = sr.Recognizer()
        self.audio_dir = os.path.join(DATABASE_DIR, "speaking")
        os.makedirs(self.audio_dir, exist_ok=True)

        # Recording holati
        self.is_recording = False
        self.recorded_frames = []
        self.audio_interface = None
        self.stream = None

        # Audio sozlamalari
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100

    # ─── OVOZ YOZISH ────────────────────────────────────────

    def start_recording(self):
        """Ovoz yozishni boshlash"""
        self.recorded_frames = []
        self.is_recording = True
        self.audio_interface = pyaudio.PyAudio()

        self.stream = self.audio_interface.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        def record():
            while self.is_recording:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.recorded_frames.append(data)

        self.record_thread = threading.Thread(target=record, daemon=True)
        self.record_thread.start()
        print("🎙️ Yozish boshlandi...")

    def stop_recording(self):
        """Ovoz yozishni to'xtatish"""
        self.is_recording = False
        time.sleep(0.3)

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio_interface:
            self.audio_interface.terminate()

        # Fayl saqlash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"speaking_{timestamp}.wav"
        filepath = os.path.join(self.audio_dir, filename)

        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio_interface.get_sample_size(self.FORMAT) if self.audio_interface else 2)
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.recorded_frames))

        print(f"✅ Yozildi: {filename}")
        return filepath

    # ─── OVOZNI MATNGA AYLANTIRISH ──────────────────────────

    def transcribe(self, audio_filepath):
        """
        Whisper yoki Google Speech Recognition ishlatish
        """
        # 1. Whisper (offline, aniqroq)
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_filepath, language="en")
            transcript = result["text"].strip()
            print(f"📝 Whisper: {transcript[:100]}...")
            return transcript
        except ImportError:
            pass

        # 2. Google Speech Recognition (online, bepul)
        try:
            with sr.AudioFile(audio_filepath) as source:
                audio = self.recognizer.record(source)
            transcript = self.recognizer.recognize_google(audio, language="en-US")
            print(f"📝 Google STT: {transcript[:100]}...")
            return transcript
        except Exception as e:
            print(f"❌ STT xatosi: {e}")
            return ""

    # ─── SPEAKING MASHQ ─────────────────────────────────────

    def run_practice_session(self, part_name="Part1", callback=None):
        """
        To'liq speaking mashq sessiyasi
        callback: UI ga natija qaytarish uchun
        """
        print(f"\n🎤 Speaking {part_name} boshlandi")

        # Savollar generatsiya
        level_map = {
            "Part1": ("B1", 3, 5),
            "Part2": ("B2", 3, 30),
            "Part3": ("C1", 2, 60)
        }
        level, count, prep_time = level_map.get(part_name, ("B2", 3, 30))

        questions_data = self.ai.generate_speaking_questions(part_name, level, count)
        if "error" in questions_data:
            print("❌ Savollar generatsiya xatosi")
            return None

        questions = questions_data.get("questions", [])
        all_results = []
        total_score = 0

        for q in questions:
            print(f"\n📌 Savol {q['id']}: {q['question']}")
            print(f"⏱️  Tayyorlanish: {prep_time} soniya")

            if callback:
                callback("question", {
                    "question": q["question"],
                    "prep_time": prep_time,
                    "question_id": q["id"],
                    "total": len(questions)
                })

            time.sleep(prep_time)

            # Yozish
            print("🎙️ Gapiring... (10 soniya)")
            if callback:
                callback("recording_start", {})

            self.start_recording()
            time.sleep(10)
            audio_path = self.stop_recording()

            if callback:
                callback("recording_stop", {"audio_path": audio_path})

            # Transkripsiya
            print("🔄 Tahlil qilinmoqda...")
            if callback:
                callback("analyzing", {})

            transcript = self.transcribe(audio_path)

            if not transcript:
                print("⚠️  Ovoz aniqlanmadi")
                continue

            # AI baholash
            result = self.ai.evaluate_speaking(q["question"], transcript)
            if "error" not in result:
                score = result.get("overall", 0)
                total_score += score
                all_results.append({
                    "question": q["question"],
                    "transcript": transcript,
                    "result": result
                })

                print(f"✅ Ball: {score}/100")
                print(f"   Fluency: {result['scores']['Fluency']['score']}")
                print(f"   Grammar: {result['scores']['Grammar']['score']}")
                print(f"   Vocabulary: {result['scores']['Vocabulary']['score']}")
                print(f"   Pronunciation: {result['scores']['Pronunciation']['score']}")

                if callback:
                    callback("result", {
                        "question": q["question"],
                        "transcript": transcript,
                        "scores": result["scores"],
                        "overall": score,
                        "feedback": result.get("ai_feedback", ""),
                        "improvements": result.get("improvements", []),
                        "better_phrases": result.get("better_phrases", [])
                    })

        # Sessiya yakunlash
        if all_results:
            avg_score = total_score / len(all_results)
            session_id = self.db.save_session(
                skill="Speaking",
                score=int(avg_score),
                max_score=100,
                duration=len(questions) * 2,
                details={"part": part_name, "results": all_results}
            )

            # Study DNA yangilash
            self.db.update_study_dna(
                "Speaking", part_name,
                correct=len([r for r in all_results if r["result"].get("overall", 0) >= 60]),
                total=len(all_results)
            )

            # Progress yangilash
            self.db.update_progress("speaking", int(avg_score * 0.75))

            final_result = {
                "part": part_name,
                "total_questions": len(questions),
                "answered": len(all_results),
                "average_score": round(avg_score, 1),
                "session_id": session_id,
                "results": all_results
            }

            if callback:
                callback("session_complete", final_result)

            return final_result

        return None

    # ─── MOCK IMTIHON ───────────────────────────────────────

    def run_mock_exam(self, callback=None):
        """
        To'liq speaking mock imtihoni (Part 1 + 2 + 3)
        """
        print("\n🎓 Speaking Mock Imtihon boshlandi!")
        all_parts = {}

        for part in ["Part1", "Part2", "Part3"]:
            print(f"\n━━━ {part} ━━━")
            result = self.run_practice_session(part, callback)
            if result:
                all_parts[part] = result

        # Umumiy ball
        if all_parts:
            overall = sum(
                p["average_score"] for p in all_parts.values()
            ) / len(all_parts)

            cefr = self._score_to_cefr(overall)
            print(f"\n🏆 Speaking Mock Yakunlandi!")
            print(f"   Umumiy ball: {round(overall, 1)}/100")
            print(f"   CEFR daraja: {cefr}")

            return {
                "type": "mock_exam",
                "overall": round(overall, 1),
                "cefr_level": cefr,
                "parts": all_parts
            }

    # ─── YORDAMCHI ──────────────────────────────────────────

    def _score_to_cefr(self, score):
        if score >= 85:
            return "C1"
        elif score >= 65:
            return "B2"
        elif score >= 50:
            return "B1"
        elif score >= 35:
            return "A2"
        else:
            return "A1"

    def get_speaking_stats(self):
        """Speaking statistikasi"""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_sessions,
                AVG(score) as avg_score,
                MAX(score) as best_score,
                MIN(score) as lowest_score
            FROM sessions
            WHERE skill='Speaking'
        """)
        stats = dict(cursor.fetchone())
        self.db.close()
        return stats

    def get_improvement_tips(self):
        """Study DNA dan zaif joylarni olib, tavsiya berish"""
        weak = self.db.get_weak_points(threshold=60)
        speaking_weak = [w for w in weak if w["skill"] == "Speaking"]

        if not speaking_weak:
            return "✅ Speaking barcha qismlari yaxshi!"

        tips = []
        for w in speaking_weak:
            part = w["question_type"]
            pct = w["percentage"]
            if part == "Part1":
                tips.append(f"Part1 ({pct}%): Shaxsiy savollar — qisqa, aniq javoblar bering")
            elif part == "Part2":
                tips.append(f"Part2 ({pct}%): Rasm tavsifi — WHAT, WHERE, WHO, WHY tuzilmasini ishlating")
            elif part == "Part3":
                tips.append(f"Part3 ({pct}%): Argumentli nutq — POINT, REASON, EXAMPLE, SUMMARY")

        return "\n".join(tips)


# Test
if __name__ == "__main__":
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    speaking = SpeakingModule(db, ai)
    print("✅ Speaking Module tayyor!")
    stats = speaking.get_speaking_stats()
    print("📊 Statistika:", stats)
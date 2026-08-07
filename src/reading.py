import os
import json
import time
import PyPDF2
from datetime import datetime
from config.settings import DATABASE_DIR, READING_RULES

class ReadingModule:
    def __init__(self, db, ai_engine):
        self.db = db
        self.ai = ai_engine
        self.reading_dir = os.path.join(DATABASE_DIR, "reading")
        os.makedirs(self.reading_dir, exist_ok=True)

    # ─── PDF O'QISH ─────────────────────────────────────────

    def extract_text_from_pdf(self, pdf_path):
        """PDF dan matn ajratib olish"""
        try:
            text = ""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            print(f"✅ PDF o'qildi: {len(text)} belgi")
            return text.strip()
        except Exception as e:
            print(f"❌ PDF xatosi: {e}")
            return ""

    def extract_text_from_txt(self, txt_path):
        """TXT fayldan matn olish"""
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"❌ TXT xatosi: {e}")
            return ""

    def get_text_from_material(self, material):
        """Material turига qarab matn olish"""
        path = material.get("file_path", "")
        if path.endswith(".pdf"):
            return self.extract_text_from_pdf(path)
        elif path.endswith(".txt"):
            return self.extract_text_from_txt(path)
        return ""

    # ─── SAVOLLAR GENERATSIYA ───────────────────────────────

    def generate_full_test(self, text, parts=None):
        """
        Matn asosida to'liq reading testi yaratish
        parts: None = barcha 6 part, yoki ["Part1", "Part2"] kabi
        """
        if parts is None:
            parts = list(READING_RULES["parts"].keys())

        print(f"\n📖 Reading testi generatsiya: {len(parts)} part")
        test_data = {
            "text": text,
            "parts": {},
            "total_questions": 0,
            "created_at": datetime.now().isoformat()
        }

        for part_name in parts:
            rule = READING_RULES["parts"].get(part_name, {})
            level = rule.get("level", "B2")
            count = rule.get("questions", 5)
            q_type = rule.get("type", "multiple_choice")

            print(f"  ⏳ {part_name} ({level}, {q_type}, {count} savol)...")

            questions = self.ai.generate_reading_questions(
                text=text,
                part_name=part_name,
                level=level,
                question_type=q_type,
                count=count
            )

            if "error" not in questions:
                test_data["parts"][part_name] = {
                    "level": level,
                    "question_type": q_type,
                    "questions": questions,
                    "count": count
                }
                test_data["total_questions"] += count
                print(f"  ✅ {part_name}: {count} savol tayyor")
            else:
                print(f"  ❌ {part_name}: xato")

        return test_data

    # ─── TEST SESSIYASI ─────────────────────────────────────

    def run_practice_session(self, parts=None, callback=None):
        """
        To'liq reading mashq sessiyasi
        """
        print("\n📖 Reading sessiyasi boshlandi")

        # Material olish
        material = self.db.get_unused_material("reading", "pdf")
        if not material:
            material = self.db.get_unused_material("reading", "txt")

        if not material:
            print("⚠️  Material topilmadi, AI matn generatsiya qiladi")
            text = self._generate_sample_text()
            material_title = "AI Generated Text"
        else:
            text = self.get_text_from_material(material)
            material_title = material.get("title", "Unknown")
            if not text:
                text = self._generate_sample_text()

        print(f"📄 Material: {material_title}")
        print(f"📝 Matn uzunligi: {len(text.split())} so'z")

        if callback:
            callback("material_ready", {
                "title": material_title,
                "text": text[:500] + "..." if len(text) > 500 else text
            })

        # Test generatsiya
        print("⏳ Savollar tayyorlanmoqda...")
        if callback:
            callback("generating", {"message": "Savollar tayyorlanmoqda..."})

        test_data = self.generate_full_test(text, parts)

        if not test_data["parts"]:
            print("❌ Savollar generatsiya qilinmadi")
            return None

        # Vaqt boshlash
        start_time = time.time()
        all_results = {}
        total_correct = 0
        total_questions = 0

        # Har bir partni o'tkazish
        for part_name, part_data in test_data["parts"].items():
            print(f"\n━━━ {part_name} ━━━")
            rule = READING_RULES["parts"].get(part_name, {})
            level = rule.get("level", "B2")
            q_type = part_data["question_type"]
            questions_wrapper = part_data["questions"]

            # Savollarni olish
            if q_type == "matching_headings":
                questions = questions_wrapper.get("paragraphs", [])
            else:
                questions = questions_wrapper.get("questions", [])

            if callback:
                callback("part_start", {
                    "part": part_name,
                    "level": level,
                    "question_type": q_type,
                    "questions": questions,
                    "text": text
                })

            # Javoblar yig'ish (terminal mode)
            user_answers = {}
            for i, q in enumerate(questions):
                if q_type == "multiple_choice":
                    print(f"\nSavol {i+1}: {q.get('question', '')}")
                    for opt, val in q.get("options", {}).items():
                        print(f"  {opt}) {val}")
                    ans = input("Javob (A/B/C/D): ").strip().upper()
                    user_answers[str(i+1)] = ans

                elif q_type == "true_false":
                    print(f"\nSavol {i+1}: {q.get('statement', '')}")
                    ans = input("True / False / Not Given: ").strip()
                    user_answers[str(i+1)] = ans

                elif q_type == "gap_filling":
                    print(f"\nSavol {i+1}: {q.get('sentence', '')}")
                    for opt, val in enumerate(q.get("options", []), 1):
                        print(f"  {opt}) {val}")
                    ans = input("Javob: ").strip()
                    user_answers[str(i+1)] = ans

                elif q_type == "matching_headings":
                    print(f"\nParagraf {q.get('id', i+1)}: {q.get('text', '')[:100]}...")
                    headings = questions_wrapper.get("headings", [])
                    for h in headings:
                        print(f"  {h['id']}) {h['heading']}")
                    ans = input("Mos heading raqami: ").strip()
                    user_answers[str(i+1)] = ans

            # Baholash
            result = self.ai.evaluate_reading_answers(
                questions=questions,
                user_answers=user_answers,
                question_type=q_type
            )

            correct = result.get("correct", 0)
            total = result.get("total", len(questions))
            percentage = result.get("percentage", 0)

            total_correct += correct
            total_questions += total

            # Part natijasi
            all_results[part_name] = {
                "level": level,
                "correct": correct,
                "total": total,
                "percentage": percentage,
                "feedback": result.get("feedback", []),
                "question_type": q_type
            }

            print(f"\n✅ {part_name}: {correct}/{total} ({percentage}%)")

            # Study DNA yangilash
            self.db.update_study_dna(
                "Reading", q_type,
                correct=correct,
                total=total
            )

            # Part natijasini saqlash
            if callback:
                callback("part_complete", {
                    "part": part_name,
                    "correct": correct,
                    "total": total,
                    "percentage": percentage,
                    "feedback": result.get("feedback", [])
                })

        # CEFR Calculator (Rule Engine)
        cefr_result = self.ai.calculate_cefr_level("Reading", all_results)

        # Umumiy ball
        duration = int((time.time() - start_time) / 60)
        overall_pct = round(
            (total_correct / total_questions * 100), 1
        ) if total_questions > 0 else 0

        # Sessiya saqlash
        session_id = self.db.save_session(
            skill="Reading",
            score=total_correct,
            max_score=total_questions,
            duration=duration,
            details={
                "material": material_title,
                "parts": all_results,
                "cefr": cefr_result
            }
        )

        # Progress yangilash
        progress_score = int(overall_pct * 0.75)
        self.db.update_progress("reading", progress_score)

        # Material ishlatildi deb belgilash
        if material and "id" in material:
            self.db.mark_material_used(material["id"])

        final_result = {
            "material": material_title,
            "total_correct": total_correct,
            "total_questions": total_questions,
            "overall_percentage": overall_pct,
            "duration_minutes": duration,
            "cefr_result": cefr_result,
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
        print("📊 READING NATIJASI")
        print("═" * 50)

        for part_name, data in result["parts"].items():
            level = data["level"]
            correct = data["correct"]
            total = data["total"]
            pct = data["percentage"]
            bar = "█" * correct + "░" * (total - correct)
            print(f"\n{part_name} ({level}): [{bar}] {correct}/{total} ({pct}%)")

            # Xato javoblar
            for fb in data.get("feedback", []):
                if not fb.get("correct"):
                    print(f"  ❌ Savol {fb['question_id']}: "
                          f"Siz: {fb['user_answer']} → "
                          f"To'g'ri: {fb['correct_answer']}")
                    if fb.get("explanation"):
                        print(f"     💡 {fb['explanation']}")

        print(f"\n{'─' * 50}")
        print(f"Jami: {result['total_correct']}/{result['total_questions']}"
              f" ({result['overall_percentage']}%)")

        cefr = result.get("cefr_result", {})
        print(f"CEFR daraja (Rule Engine): "
              f"{cefr.get('estimated_level', 'N/A')}")

        breakdown = cefr.get("breakdown", {})
        for lvl, data in breakdown.items():
            print(f"  {lvl}: {data['correct']}/{data['total']}"
                  f" ({data['percentage']}%)")

        print("═" * 50)

    # ─── MOCK IMTIHON ───────────────────────────────────────

    def run_mock_exam(self, callback=None):
        """
        To'liq reading mock imtihoni (barcha 6 part)
        """
        print("\n🎓 Reading Mock Imtihon boshlandi!")
        print("⏱️  Vaqt: 60 daqiqa | Savollar: 35 ta")

        result = self.run_practice_session(
            parts=["Part1", "Part2", "Part3",
                   "Part4", "Part5", "Part6"],
            callback=callback
        )

        if result:
            print(f"\n🏆 Mock Imtihon Yakunlandi!")
            print(f"   Natija: {result['total_correct']}/35")
            print(f"   CEFR: {result['cefr_result']['estimated_level']}")

        return result

    # ─── QISMAN MASHQ ───────────────────────────────────────

    def run_b2_practice(self, callback=None):
        """Faqat B2 partlar (Part3, Part4)"""
        return self.run_practice_session(
            parts=["Part3", "Part4"],
            callback=callback
        )

    def run_weak_parts(self, callback=None):
        """Zaif partlarni mashq qilish"""
        weak = self.db.get_weak_points(threshold=60)
        reading_weak = [w for w in weak if w["skill"] == "Reading"]

        if not reading_weak:
            print("✅ Reading barcha qismlari yaxshi!")
            return None

        # Zaif question type dan part aniqlash
        type_to_part = {
            "multiple_choice": "Part1",
            "true_false": "Part2",
            "matching_headings": "Part3",
            "gap_filling": "Part4",
            "inference": "Part5",
            "summary_completion": "Part6"
        }

        weak_parts = []
        for w in reading_weak:
            part = type_to_part.get(w["question_type"])
            if part and part not in weak_parts:
                weak_parts.append(part)

        print(f"\n🎯 Zaif partlar: {', '.join(weak_parts)}")
        return self.run_practice_session(
            parts=weak_parts,
            callback=callback
        )

    # ─── AI MATN GENERATSIYA ────────────────────────────────

    def _generate_sample_text(self):
        """Material bo'lmasa AI matn yaratadi"""
        system = "Generate a B2-level reading passage. Plain text only."
        prompt = """Write a 400-word academic reading passage about 
        technology and society suitable for CEFR B2 exam."""
        return self.ai._send(system, prompt, max_tokens=600)

    # ─── STATISTIKA ─────────────────────────────────────────

    def get_reading_stats(self):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_sessions,
                AVG(percentage) as avg_percentage,
                MAX(percentage) as best,
                MIN(percentage) as lowest
            FROM sessions
            WHERE skill='Reading'
        """)
        stats = dict(cursor.fetchone())
        self.db.close()
        return stats

    def get_improvement_tips(self):
        weak = self.db.get_weak_points(threshold=60)
        reading_weak = [w for w in weak if w["skill"] == "Reading"]
        tips = []
        tip_map = {
            "multiple_choice": "Part1: Savolni avval o'qing, keyin matnda javob qidiring",
            "true_false": "Part2: 'Not Given' — matнda umuman aytilmagan bo'lsa",
            "matching_headings": "Part3: Har paragrafning asosiy g'oyasini toping",
            "gap_filling": "Part4: Bo'sh joy atrofidagi so'zlarga e'tibor bering",
            "inference": "Part5: Bevosita aytilmagan narsani kontekstdan aniqlang",
            "summary_completion": "Part6: Summary ni avval o'qib, keyin matнda qidiring"
        }
        for w in reading_weak:
            tip = tip_map.get(w["question_type"], "")
            if tip:
                tips.append(f"{tip} ({w['percentage']}%)")
        return "\n".join(tips) if tips else "✅ Reading yaxshi ketmoqda!"


# Test
if __name__ == "__main__":
    from src.database import Database
    from src.ai_engine import AIEngine
    db = Database()
    ai = AIEngine(db)
    reading = ReadingModule(db, ai)
    print("✅ Reading Module tayyor!")
    stats = reading.get_reading_stats()
    print("📊 Statistika:", stats)
    tips = reading.get_improvement_tips()
    print("💡 Tavsiyalar:", tips)
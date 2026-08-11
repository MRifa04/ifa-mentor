import json
import os
import re
from datetime import datetime


class PDFAnalyzer:
    def __init__(self, ai):
        self.ai = ai
        self.rules_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),
            "config", "exam_rules.json"
        )

    # ── PDF O'QISH ──────────────────────────────────────────

    def extract_text(self, pdf_path):
        """PDF dan matn olish"""
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"❌ PDF o'qish xatosi: {e}")
            return ""

    # ── AI TAHLIL ───────────────────────────────────────────

    def analyze_mock_exam(self, pdf_path):
        """
        Mock imtihon PDF ni AI bilan tahlil qilish
        """
        print(f"📄 PDF tahlil qilinmoqda: {pdf_path}")
        text = self.extract_text(pdf_path)

        if not text:
            return None

        system = """You are a CEFR exam structure analyzer.
Analyze the exam PDF and extract structure.
Return ONLY valid JSON, no markdown."""

        prompt = f"""
Analyze this exam document and extract its structure.
Text (first 3000 chars): {text[:3000]}

Return ONLY valid JSON:
{{
  "exam_type": "multilevel_cefr",
  "detected_skills": ["Listening", "Reading", "Writing", "Speaking"],
  "total_questions": 35,
  "total_time_minutes": 180,
  "sections": [
    {{
      "skill": "Reading",
      "parts": [
        {{
          "part_name": "Part 1",
          "level": "B1",
          "question_type": "multiple_choice",
          "questions_count": 5,
          "points_per_question": 1,
          "instructions": "..."
        }}
      ],
      "total_questions": 15,
      "time_minutes": 60
    }}
  ],
  "scoring": {{
    "total_points": 75,
    "passing_score": 45,
    "b2_minimum": 51,
    "c1_minimum": 65
  }},
  "notes": "Additional exam notes..."
}}"""

        result = self.ai._send(system, prompt, max_tokens=2000)

        try:
            clean = result.strip().replace(
                "```json", ""
            ).replace("```", "")
            data = json.loads(clean)
            return data
        except Exception as e:
            print(f"❌ JSON parse xatosi: {e}")
            return self._fallback_analysis(text)

    def _fallback_analysis(self, text):
        """
        AI ishlamasa — regex bilan tahlil
        """
        analysis = {
            "exam_type": "multilevel_cefr",
            "detected_skills": [],
            "total_questions": 0,
            "sections": []
        }

        text_lower = text.lower()

        # Skilllarni aniqlash
        skill_map = {
            "listening": "Listening",
            "reading": "Reading",
            "writing": "Writing",
            "speaking": "Speaking"
        }
        for key, skill in skill_map.items():
            if key in text_lower:
                analysis["detected_skills"].append(skill)

        # Savol sonini aniqlash
        numbers = re.findall(
            r'(\d+)\s*(?:questions?|savollar?)',
            text_lower
        )
        if numbers:
            analysis["total_questions"] = max(
                int(n) for n in numbers
            )

        return analysis

    # ── QOIDALARNI YANGILASH ────────────────────────────────

    def update_exam_rules(self, analysis):
        """
        Tahlil natijasini exam_rules.json ga saqlash
        """
        if not analysis:
            return False

        try:
            # Mavjud qoidalarni yuklash
            with open(
                self.rules_path, "r", encoding="utf-8"
            ) as f:
                rules = json.load(f)

            # Yangi ma'lumotlarni qo'shish
            rules["last_updated"] = (
                datetime.now().isoformat()
            )
            rules["source"] = "pdf_analysis"

            # Scoring yangilash
            if "scoring" in analysis:
                scoring = analysis["scoring"]
                if "b2_minimum" in scoring:
                    rules["levels"]["B2"]["min"] = (
                        scoring["b2_minimum"]
                    )
                if "c1_minimum" in scoring:
                    rules["levels"]["C1"]["min"] = (
                        scoring["c1_minimum"]
                    )

            # Sectionlarni yangilash
            if "sections" in analysis:
                for section in analysis["sections"]:
                    skill = section.get("skill", "")
                    if skill in rules.get("skills", {}):
                        parts = section.get("parts", [])
                        if parts:
                            updated_parts = {}
                            for part in parts:
                                part_name = part.get(
                                    "part_name", "Part1"
                                ).replace(" ", "")
                                updated_parts[part_name] = {
                                    "level": part.get(
                                        "level", "B2"
                                    ),
                                    "questions": part.get(
                                        "questions_count", 5
                                    ),
                                    "type": part.get(
                                        "question_type",
                                        "multiple_choice"
                                    )
                                }
                            rules["skills"][skill][
                                "parts"
                            ] = updated_parts

            # Saqlash
            with open(
                self.rules_path, "w", encoding="utf-8"
            ) as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)

            print("✅ exam_rules.json yangilandi!")
            return True

        except Exception as e:
            print(f"❌ Qoidalar yangilash xatosi: {e}")
            return False

    # ── TO'LIQ JARAYON ──────────────────────────────────────

    def process_mock_pdf(self, pdf_path):
        """
        PDF ni to'liq qayta ishlash
        1. O'qish
        2. Tahlil
        3. Qoidalar yangilash
        """
        print(f"\n📊 Mock PDF qayta ishlanmoqda...")

        # Tahlil
        analysis = self.analyze_mock_exam(pdf_path)
        if not analysis:
            return {
                "success": False,
                "error": "PDF tahlil qilinmadi"
            }

        # Qoidalar yangilash
        updated = self.update_exam_rules(analysis)

        result = {
            "success": True,
            "pdf_path": pdf_path,
            "analysis": analysis,
            "rules_updated": updated,
            "detected_skills": analysis.get(
                "detected_skills", []
            ),
            "total_questions": analysis.get(
                "total_questions", 0
            )
        }

        print(f"✅ Tahlil tugadi:")
        print(f"   Skilllar: {result['detected_skills']}")
        print(f"   Savollar: {result['total_questions']}")

        return result

    # ── MATERIALLARNI TEKSHIRISH ─────────────────────────────

    def scan_library_for_mocks(self, database_dir):
        """
        Library da mock PDF larni topish va tahlil
        """
        results = []
        mock_dir = os.path.join(database_dir, "tests")

        if not os.path.exists(mock_dir):
            return results

        for filename in os.listdir(mock_dir):
            if filename.endswith(".pdf"):
                path = os.path.join(mock_dir, filename)
                if any(
                    word in filename.lower()
                    for word in ["mock", "test", "exam", "full"]
                ):
                    print(f"\n🔍 Mock topildi: {filename}")
                    result = self.process_mock_pdf(path)
                    results.append(result)

        return results
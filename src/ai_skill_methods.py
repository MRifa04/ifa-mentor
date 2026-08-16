"""AI Engine skill metodlari — Writing, Reading, Listening, Speaking, Vocabulary."""

import json
import re
import random


class AISkillMixin:
    """AIEngine uchun skill-specific metodlar."""

    def _parse_json(self, text):
        if not text:
            return None

        text = str(text).strip()
        if text.startswith("```"):
            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )
            text = re.sub(r"\s*```$", "", text)

        for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
            match = re.search(pattern, text)
            if not match:
                continue
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _json_send(self, system, user_msg, max_tokens=2000):
        prompt = (
            f"{system}\n\n"
            "IMPORTANT: Reply with valid JSON only. "
            "No markdown, no explanation outside JSON.\n\n"
            f"USER REQUEST:\n{user_msg}"
        )
        raw = self._send("", prompt, max_tokens=max_tokens)
        data = self._parse_json(raw)
        if data is None:
            return {"error": raw or "JSON parse xatosi"}
        return data

    # ── WRITING ─────────────────────────────────────────────

    def generate_writing_prompt(self, task_type="formal_letter", level="B2"):
        system = (
            "You are a CEFR B2 writing examiner. "
            "Return JSON only."
        )
        user_msg = f"""
Create one writing task.
task_type: {task_type}
level: {level}

JSON schema:
{{
  "task_type": "{task_type}",
  "level": "{level}",
  "topic": "short topic",
  "instructions": "full task instructions",
  "min_words": 150,
  "time_minutes": 30,
  "points_to_cover": ["point 1", "point 2", "point 3"]
}}
"""
        data = self._json_send(system, user_msg)
        if "error" in data:
            return self._writing_prompt_fallback(task_type, level)
        return data

    def _writing_prompt_fallback(self, task_type, level):
        fallbacks = {
            "formal_letter": {
                "task_type": "formal_letter",
                "level": level,
                "topic": "Complaining about a product",
                "instructions": (
                    "Write a formal letter to customer service "
                    "complaining about a faulty product."
                ),
                "min_words": 150,
                "time_minutes": 30,
                "points_to_cover": [
                    "What you bought and when",
                    "Describe the problem",
                    "What action you want",
                ],
            },
            "argumentative_essay": {
                "task_type": "argumentative_essay",
                "level": level,
                "topic": "Technology in education",
                "instructions": (
                    "Technology brings more problems than benefits "
                    "to education. To what extent do you agree?"
                ),
                "min_words": 250,
                "time_minutes": 40,
                "points_to_cover": [
                    "Clear position",
                    "Two arguments with examples",
                    "Opposing view",
                    "Strong conclusion",
                ],
            },
        }
        return fallbacks.get(
            task_type,
            fallbacks["formal_letter"],
        )

    def evaluate_writing(
        self,
        task_type="formal_letter",
        prompt_text="",
        user_essay="",
    ):
        system = (
            "You are a CEFR writing examiner. "
            "Score fairly. Return JSON only."
        )
        user_msg = f"""
Evaluate this essay.

Task type: {task_type}
Prompt: {prompt_text}
Essay:
{user_essay[:6000]}

JSON schema:
{{
  "overall": 3.5,
  "cefr_level": "B2",
  "scores": {{
    "Task Achievement": 3.5,
    "Coherence": 3.5,
    "Vocabulary": 3.5,
    "Grammar": 3.5
  }},
  "strengths": ["..."],
  "improvements": ["..."],
  "feedback": "short summary"
}}
overall is 0-5 scale.
"""
        data = self._json_send(system, user_msg, max_tokens=2500)
        if "error" not in data:
            return data

        words = len(user_essay.split())
        base = min(4.5, 2.0 + words / 120)
        return {
            "overall": round(base, 1),
            "cefr_level": "B1" if base < 3 else "B2",
            "scores": {
                "Task Achievement": round(base, 1),
                "Coherence": round(base - 0.2, 1),
                "Vocabulary": round(base - 0.1, 1),
                "Grammar": round(base - 0.3, 1),
            },
            "strengths": ["Essay submitted successfully"],
            "improvements": [
                "Add more linking words",
                "Check grammar accuracy",
            ],
            "feedback": (
                "AI offline rejimida taxminiy baho berildi."
            ),
        }

    # ── READING ─────────────────────────────────────────────

    def generate_reading_questions(
        self,
        text="",
        part_name="Part3",
        level="B2",
        question_type="multiple_choice",
        count=5,
    ):
        system = "You are a CEFR reading test creator. JSON only."
        user_msg = f"""
Create {count} reading questions.

Part: {part_name}
Level: {level}
Question type: {question_type}

Text:
{text[:5000]}

JSON schema:
{{
  "questions": [
    {{
      "id": 1,
      "question": "question text",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "A"
    }}
  ]
}}
"""
        data = self._json_send(system, user_msg, max_tokens=3000)
        if "error" not in data and data.get("questions"):
            return data
        return self._reading_questions_fallback(
            count,
            question_type,
        )

    def _reading_questions_fallback(self, count, question_type):
        questions = []
        for i in range(1, count + 1):
            questions.append({
                "id": i,
                "question": (
                    f"According to the text, what is true "
                    f"about point {i}?"
                ),
                "options": {
                    "A": "Option A",
                    "B": "Option B",
                    "C": "Option C",
                    "D": "Option D",
                },
                "correct_answer": "A",
            })
        return {"questions": questions, "q_type": question_type}

    def evaluate_reading_answers(
        self,
        questions=None,
        user_answers=None,
        question_type="multiple_choice",
    ):
        questions = questions or []
        user_answers = user_answers or {}
        correct = 0
        feedback = []

        for index, q in enumerate(questions, start=1):
            key = str(index)
            user_ans = str(user_answers.get(key, "")).strip().upper()
            correct_ans = str(
                q.get("correct_answer", "A")
            ).strip().upper()
            is_ok = user_ans == correct_ans
            if is_ok:
                correct += 1
            feedback.append({
                "question": index,
                "correct": is_ok,
                "your_answer": user_ans,
                "correct_answer": correct_ans,
            })

        total = len(questions) or 1
        percentage = round(correct / total * 100, 1)
        return {
            "correct": correct,
            "total": total,
            "percentage": percentage,
            "feedback": feedback,
        }

    def calculate_cefr_level(self, skill, all_results):
        if not all_results:
            return {"level": "B1", "score": 41}

        percentages = [
            part.get("percentage", 0)
            for part in all_results.values()
            if isinstance(part, dict)
        ]
        avg = sum(percentages) / len(percentages) if percentages else 0

        if avg >= 86:
            level = "C1"
            score = 68
        elif avg >= 70:
            level = "B2"
            score = 56
        elif avg >= 50:
            level = "B1"
            score = 45
        else:
            level = "A2"
            score = 32

        return {
            "skill": skill,
            "level": level,
            "score": score,
            "average_percentage": round(avg, 1),
        }

    # ── LISTENING ───────────────────────────────────────────

    def generate_listening_questions(
        self,
        transcript="",
        part_name="Part3",
        level="B2",
        question_type="multiple_choice",
        count=5,
    ):
        system = "You are a CEFR listening test creator. JSON only."
        user_msg = f"""
Create {count} listening comprehension questions.

Part: {part_name}
Level: {level}
Type: {question_type}

Transcript:
{transcript[:5000]}

JSON schema:
{{
  "questions": [
    {{
      "id": 1,
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "A"
    }}
  ]
}}
"""
        data = self._json_send(system, user_msg, max_tokens=3000)
        if "error" not in data and data.get("questions"):
            return data
        return self._reading_questions_fallback(
            count,
            question_type,
        )

    # ── SPEAKING ────────────────────────────────────────────

    def generate_speaking_questions(
        self,
        part_name="Part1",
        level="B2",
        count=3,
    ):
        system = "You are a CEFR speaking examiner. JSON only."
        user_msg = f"""
Create {count} speaking questions for {part_name} at {level}.

JSON schema:
{{
  "questions": [
    {{"id": 1, "question": "Tell me about your hometown."}}
  ]
}}
"""
        data = self._json_send(system, user_msg)
        if "error" not in data and data.get("questions"):
            return data

        defaults = {
            "Part1": [
                "Tell me about your hometown.",
                "What do you like doing in your free time?",
                "Do you prefer studying alone or in a group?",
            ],
            "Part2": [
                "Describe a place you would like to visit.",
                "Talk about a skill you want to learn.",
            ],
            "Part3": [
                "How has technology changed education?",
                "Should students learn more practical skills?",
            ],
        }
        prompts = defaults.get(part_name, defaults["Part1"])
        questions = [
            {"id": i + 1, "question": q}
            for i, q in enumerate(prompts[:count])
        ]
        return {"questions": questions}

    def evaluate_speaking(self, question, transcript):
        system = "You are a CEFR speaking examiner. JSON only."
        user_msg = f"""
Evaluate this speaking response.

Question: {question}
Transcript: {transcript[:3000]}

JSON schema:
{{
  "overall": 3.5,
  "cefr_level": "B2",
  "scores": {{
    "Fluency": 3.5,
    "Grammar": 3.5,
    "Pronunciation": 3.5,
    "Vocabulary": 3.5
  }},
  "feedback": "short feedback",
  "strengths": ["..."],
  "improvements": ["..."]
}}
overall is 0-5.
"""
        data = self._json_send(system, user_msg)
        if "error" not in data:
            return data

        words = len(transcript.split())
        base = min(4.5, 2.0 + words / 25)
        return {
            "overall": round(base, 1),
            "cefr_level": "B1" if base < 3 else "B2",
            "scores": {
                "Fluency": round(base, 1),
                "Grammar": round(base - 0.2, 1),
                "Pronunciation": round(base - 0.1, 1),
                "Vocabulary": round(base, 1),
            },
            "feedback": "Taxminiy baho (offline rejim).",
            "strengths": ["Response recorded"],
            "improvements": ["Use more complex sentences"],
        }

    # ── VOCABULARY ──────────────────────────────────────────

    def analyze_vocabulary(self, text, source=""):
        system = (
            "You are a vocabulary expert for CEFR B2. JSON only."
        )
        user_msg = f"""
Extract useful B2-level words from this text.
Source: {source}

Text:
{text[:4000]}

JSON schema:
{{
  "words": [
    {{
      "word": "achieve",
      "uzbek": "erishmoq",
      "definition": "...",
      "pronunciation": "...",
      "level": "B2",
      "ai_example": "...",
      "example_from_text": "...",
      "collocations": ["..."]
    }}
  ]
}}
Max 10 words.
"""
        data = self._json_send(system, user_msg, max_tokens=2500)
        if "error" not in data and data.get("words"):
            return data
        return {"words": [], "error": data.get("error")}

    def generate_vocabulary_exercise(
        self,
        word="",
        uzbek="",
        example="",
    ):
        system = "You are a vocabulary teacher. JSON only."
        user_msg = f"""
Create exercises for: {word} ({uzbek})
Example: {example}

JSON schema:
{{
  "exercises": {{
    "gap_fill": {{
      "sentence": "I want to ___ my goals.",
      "answer": "{word}"
    }},
    "speaking_prompt": "Use '{word}' in a sentence about your goals.",
    "writing_prompt": "Write 2 sentences using '{word}'."
  }}
}}
"""
        data = self._json_send(system, user_msg)
        if "error" not in data:
            return data
        return {
            "exercises": {
                "gap_fill": {
                    "sentence": f"Complete: {word} means ___ in Uzbek.",
                    "answer": uzbek or word,
                },
                "speaking_prompt": (
                    f"Use the word '{word}' in a sentence."
                ),
                "writing_prompt": (
                    f"Write two sentences with '{word}'."
                ),
            }
        }

    # ── MOCK EXAM ───────────────────────────────────────────

    def generate_mock_exam_result(self, skill, current_score=40):
        """Mock imtihon uchun qisqa AI bahosi."""
        skill_title = skill.title()
        system = "You are a CEFR mock exam assessor. JSON only."
        user_msg = f"""
Give a mock exam result for {skill_title}.
Current learner score: {current_score}/75.

JSON schema:
{{
  "skill": "{skill_title}",
  "score": 52,
  "max_score": 75,
  "percentage": 69,
  "level": "B2",
  "summary": "one sentence feedback",
  "strengths": ["..."],
  "weaknesses": ["..."]
}}
"""
        data = self._json_send(system, user_msg)
        if "error" not in data:
            return data

        delta = random.randint(-3, 6)
        score = max(20, min(75, int(current_score) + delta))
        return {
            "skill": skill_title,
            "score": score,
            "max_score": 75,
            "percentage": int(score / 75 * 100),
            "level": "B2" if score >= 51 else "B1",
            "summary": f"{skill_title} mock imtihon yakunlandi.",
            "strengths": ["Completed mock exam"],
            "weaknesses": ["Practice more under time pressure"],
        }

    def check_tense_sentence(self, tense_key, sentence):
        """Foydalanuvchi tuzgan gapni tekshirish."""
        from src.tenses.registry import get_tense

        tense = get_tense(tense_key)
        name = tense["name"] if tense else tense_key
        system = "You are an English grammar teacher. JSON only."
        user_msg = f"""
Check if this sentence correctly uses {name}.

Sentence: {sentence}

JSON schema:
{{
  "correct": true,
  "feedback": "explanation in Uzbek why correct or wrong",
  "correction": "corrected sentence if needed or empty"
}}
"""
        data = self._json_send(system, user_msg)
        if "error" not in data:
            return {
                "correct": bool(data.get("correct")),
                "feedback": data.get("feedback", ""),
                "skill": "creation",
            }
        words = len(sentence.split())
        return {
            "correct": words >= 5,
            "feedback": (
                "Gap qabul qilindi (offline tekshiruv)."
                if words >= 5 else "Kamida 5 so'z yozing."
            ),
            "skill": "creation",
        }

    def explain_tense_mistake(self, tense_key, wrong, correct):
        system = "English grammar teacher. Reply in Uzbek. Be concise."
        user_msg = (
            f"Tense: {tense_key}\n"
            f"Wrong: {wrong}\nCorrect: {correct}\n"
            "Explain WHY the wrong form is incorrect."
        )
        return self._send(system, user_msg, max_tokens=400)

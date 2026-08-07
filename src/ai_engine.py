import anthropic
import json
import os
from config.settings import ANTHROPIC_API_KEY, USER_NAME, CURRENT_SCORES
from config.settings import CEFR_LEVELS, READING_RULES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class AIEngine:
    def __init__(self, db):
        self.db = db
        self.client = client
        self.model = "claude-sonnet-4-6"
        self.conversation_history = []

    def _send(self, system, user_msg, max_tokens=1000):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_msg}]
            )
            return response.content[0].text
        except Exception as e:
            return f"AI xatosi: {e}"

    def _send_with_history(self, system, max_tokens=1000):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=self.conversation_history
            )
            reply = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })
            return reply
        except Exception as e:
            return f"AI xatosi: {e}"

    def chat(self, user_message):
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        system = f"""You are IFA Mentor, a personal CEFR exam coach for {USER_NAME}.

Current scores:
- Listening: {CURRENT_SCORES['listening']}/75
- Reading: {CURRENT_SCORES['reading']}/75
- Writing: {CURRENT_SCORES['writing']}/75
- Speaking: {CURRENT_SCORES['speaking']}/75
- Overall: {CURRENT_SCORES['overall']}/75

Current level: B1. Target: B2 (overall 51+).
Weakest skill: Speaking (35).

Rules:
- Always respond in the same language the user writes in
- Be encouraging but honest
- Give specific, actionable advice
- Keep responses concise"""
        return self._send_with_history(system)

    def clear_history(self):
        self.conversation_history = []

    # ─── READING ────────────────────────────────────────────

    def generate_reading_questions(self, text, part_name, level, question_type, count):
        system = """You are a CEFR exam question generator.
Generate exam questions exactly in JSON format. No extra text, only JSON."""

        prompts = {
            "multiple_choice": f"""
Text: {text[:2000]}
Generate {count} multiple choice questions for {part_name} ({level} level).
JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "B",
      "explanation": "..."
    }}
  ]
}}""",
            "true_false": f"""
Text: {text[:2000]}
Generate {count} True/False/Not Given questions for {part_name} ({level} level).
JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "statement": "...",
      "answer": "True",
      "explanation": "..."
    }}
  ]
}}""",
            "matching_headings": f"""
Text: {text[:2000]}
Generate {count} matching headings questions for {part_name} ({level} level).
JSON format:
{{
  "paragraphs": [
    {{"id": "A", "text": "first 50 words of paragraph..."}}
  ],
  "headings": [
    {{"id": 1, "heading": "..."}}
  ],
  "answers": {{"A": 1, "B": 3}}
}}""",
            "gap_filling": f"""
Text: {text[:2000]}
Generate {count} gap filling questions for {part_name} ({level} level).
JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "sentence": "The economy is ___ rapidly.",
      "answer": "growing",
      "options": ["growing", "fallen", "stable", "reduced"]
    }}
  ]
}}"""
        }

        prompt = prompts.get(question_type, prompts["multiple_choice"])
        result = self._send(system, prompt, max_tokens=2000)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def evaluate_reading_answers(self, questions, user_answers, question_type):
        correct = 0
        total = len(questions)
        feedback = []

        for i, q in enumerate(questions):
            user_ans = user_answers.get(str(i+1), "")
            if question_type == "multiple_choice":
                is_correct = user_ans.upper() == q["answer"].upper()
            elif question_type == "true_false":
                is_correct = user_ans.lower() == q["answer"].lower()
            else:
                is_correct = user_ans.lower().strip() == str(q.get("answer", "")).lower().strip()

            if is_correct:
                correct += 1
            feedback.append({
                "question_id": i+1,
                "correct": is_correct,
                "user_answer": user_ans,
                "correct_answer": q.get("answer", ""),
                "explanation": q.get("explanation", "")
            })

        return {
            "correct": correct,
            "total": total,
            "percentage": round((correct/total)*100, 1) if total > 0 else 0,
            "feedback": feedback
        }

    # ─── LISTENING ──────────────────────────────────────────

    def generate_listening_questions(self, transcript, part_name, level, question_type, count):
        system = """You are a CEFR Listening exam question generator.
Generate questions based on audio transcript. JSON only, no extra text."""

        prompt = f"""
Audio transcript: {transcript[:1500]}
Part: {part_name} | Level: {level} | Type: {question_type} | Count: {count}

Generate {count} listening questions.
JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "According to the speaker, what is...?",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "timestamp": "0:45",
      "explanation": "The speaker said..."
    }}
  ]
}}"""
        result = self._send(system, prompt, max_tokens=2000)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── WRITING ────────────────────────────────────────────

    def generate_writing_prompt(self, task_type, level="B2"):
        system = """You are a CEFR Writing examiner.
Generate writing tasks. JSON only."""

        prompt = f"""
Generate a CEFR {level} writing task.
Task type: {task_type}

JSON format:
{{
  "task_type": "formal_letter",
  "level": "B2",
  "topic": "...",
  "instructions": "Write a formal letter to...",
  "min_words": 150,
  "time_minutes": 30,
  "points_to_cover": ["point 1", "point 2", "point 3"]
}}"""
        result = self._send(system, prompt)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def evaluate_writing(self, task_type, prompt_text, user_essay):
        system = """You are an expert CEFR Writing examiner.
Evaluate writing strictly according to official CEFR rubric.
Respond ONLY in JSON format."""

        rubric_prompt = f"""
Task type: {task_type}
Prompt: {prompt_text}
Student's essay:
{user_essay}

Evaluate using official CEFR rubric (each criterion 0-5):
JSON format:
{{
  "word_count": 187,
  "scores": {{
    "Task Achievement": {{"score": 3.5, "feedback": "..."}},
    "Coherence_Cohesion": {{"score": 3.0, "feedback": "..."}},
    "Lexical_Resource": {{"score": 3.5, "feedback": "..."}},
    "Grammar_Range": {{"score": 3.0, "feedback": "..."}}
  }},
  "overall": 3.25,
  "cefr_level": "B2",
  "strengths": ["Good topic sentences", "..."],
  "improvements": ["Use more linking words", "..."],
  "corrected_sentences": [
    {{"original": "...", "corrected": "...", "reason": "..."}}
  ],
  "band_feedback": "Your writing demonstrates B2 level..."
}}"""

        result = self._send(system, rubric_prompt, max_tokens=2000)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── SPEAKING ───────────────────────────────────────────

    def generate_speaking_questions(self, part_name, level, count):
        system = """You are a CEFR Speaking examiner.
Generate speaking questions. JSON only."""

        prompt = f"""
Generate {count} speaking questions for {part_name} ({level} level).
JSON format:
{{
  "part": "Part1",
  "level": "B1",
  "prep_time_seconds": 5,
  "questions": [
    {{
      "id": 1,
      "question": "Tell me about your daily routine.",
      "type": "personal",
      "expected_duration_seconds": 60,
      "key_vocabulary": ["routine", "schedule", "habit"],
      "sample_answer_points": ["mention morning activities", "work/study", "evening"]
    }}
  ]
}}"""
        result = self._send(system, prompt)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def evaluate_speaking(self, question, transcript):
        system = """You are an expert CEFR Speaking examiner.
Evaluate spoken English strictly. JSON only."""

        prompt = f"""
Question: {question}
Student's spoken answer (transcribed): {transcript}

Evaluate using CEFR Speaking rubric:
JSON format:
{{
  "scores": {{
    "Fluency": {{"score": 68, "feedback": "Good flow but paused at..."}},
    "Grammar": {{"score": 72, "feedback": "Mostly accurate..."}},
    "Vocabulary": {{"score": 65, "feedback": "Good range but..."}},
    "Pronunciation": {{"score": 70, "feedback": "Clear but..."}}
  }},
  "overall": 68,
  "cefr_level": "B2",
  "duration_seconds": 45,
  "word_count": 87,
  "strengths": ["Good opening", "Clear structure"],
  "improvements": ["Avoid repetition of 'like'", "Use more complex sentences"],
  "better_phrases": [
    {{"original": "very good", "better": "exceptional", "context": "..."}}
  ],
  "ai_feedback": "Your speaking shows B1-B2 transition..."
}}"""
        result = self._send(system, prompt, max_tokens=1500)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── VOCABULARY ─────────────────────────────────────────

    def analyze_vocabulary(self, text, source=""):
        system = """You are a vocabulary analyst for CEFR exam preparation.
Extract and analyze key vocabulary. JSON only."""

        prompt = f"""
Text: {text[:3000]}
Source: {source}

Extract 15 most important B2-level words.
JSON format:
{{
  "words": [
    {{
      "word": "sustainable",
      "uzbek": "barqaror",
      "pronunciation": "/səˈsteɪnəbl/",
      "definition": "able to continue over a long period",
      "example_from_text": "sustainable development",
      "ai_example": "We need sustainable solutions for our future.",
      "level": "B2",
      "exam_frequency": "high",
      "word_family": ["sustainability", "sustainably", "unsustainable"]
    }}
  ]
}}"""
        result = self._send(system, prompt, max_tokens=3000)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def generate_vocabulary_exercise(self, word, uzbek, example):
        system = """You are a vocabulary teacher.
Create exercises for one word. JSON only."""

        prompt = f"""
Word: {word}
Uzbek: {uzbek}
Example: {example}

Create exercises:
JSON format:
{{
  "word": "{word}",
  "exercises": {{
    "gap_fill": {{
      "sentence": "The company is working on ___ energy solutions.",
      "answer": "{word}"
    }},
    "speaking_prompt": "Use '{word}' in a sentence about your life.",
    "writing_prompt": "Write 2 sentences using '{word}'.",
    "synonyms": ["lasting", "long-term", "viable"],
    "antonyms": ["temporary", "short-term"]
  }}
}}"""
        result = self._send(system, prompt)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── DAILY PLAN ─────────────────────────────────────────

    def generate_daily_plan(self, weak_points, progress_history):
        system = """You are an AI study planner for CEFR exam preparation.
Create optimal daily study plan. JSON only."""

        prompt = f"""
Student: {USER_NAME}
Current level: B1 → Target: B2
Total daily time: 90 minutes

Weak points: {json.dumps(weak_points)}
Recent progress: {json.dumps(progress_history[-7:] if progress_history else [])}

Create today's study plan:
JSON format:
{{
  "date": "today",
  "total_minutes": 90,
  "focus_skill": "Speaking",
  "reason": "Speaking is weakest at 35/75",
  "tasks": [
    {{
      "order": 1,
      "skill": "Speaking",
      "task_type": "practice",
      "duration": 30,
      "description": "Part 2 image description practice",
      "priority": "high"
    }},
    {{
      "order": 2,
      "skill": "Writing",
      "task_type": "essay",
      "duration": 25,
      "description": "Formal letter practice",
      "priority": "medium"
    }},
    {{
      "order": 3,
      "skill": "Listening",
      "task_type": "practice",
      "duration": 20,
      "description": "Part 3-4 matching practice",
      "priority": "medium"
    }},
    {{
      "order": 4,
      "skill": "Vocabulary",
      "task_type": "review",
      "duration": 15,
      "description": "Spaced repetition review",
      "priority": "low"
    }}
  ],
  "motivational_message": "You need only +5 overall to reach B2!"
}}"""
        result = self._send(system, prompt, max_tokens=1500)
        try:
            return json.loads(result)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── CEFR CALCULATOR ────────────────────────────────────

    def calculate_cefr_level(self, skill, part_results):
        """
        Rule Engine — AI emas, formula ishlaydi
        """
        b1_correct = 0
        b1_total = 0
        b2_correct = 0
        b2_total = 0
        c1_correct = 0
        c1_total = 0

        for part, result in part_results.items():
            rules = READING_RULES["parts"].get(part, {})
            level = rules.get("level", "B2")
            correct = result.get("correct", 0)
            total = result.get("total", 0)

            if level == "B1":
                b1_correct += correct
                b1_total += total
            elif level == "B2":
                b2_correct += correct
                b2_total += total
            elif level == "C1":
                c1_correct += correct
                c1_total += total

        b1_pct = (b1_correct/b1_total*100) if b1_total > 0 else 0
        b2_pct = (b2_correct/b2_total*100) if b2_total > 0 else 0
        c1_pct = (c1_correct/c1_total*100) if c1_total > 0 else 0

        # Daraja aniqlash (deterministik)
        if c1_pct >= 60 and b2_pct >= 60 and b1_pct >= 60:
            estimated = "C1"
        elif b2_pct >= 60 and b1_pct >= 60:
            estimated = "B2"
        elif b1_pct >= 60:
            estimated = "B1"
        else:
            estimated = "A2"

        return {
            "skill": skill,
            "estimated_level": estimated,
            "breakdown": {
                "B1": {"correct": b1_correct, "total": b1_total, "percentage": round(b1_pct, 1)},
                "B2": {"correct": b2_correct, "total": b2_total, "percentage": round(b2_pct, 1)},
                "C1": {"correct": c1_correct, "total": c1_total, "percentage": round(c1_pct, 1)}
            }
        }


# Test
if __name__ == "__main__":
    from src.database import Database
    db = Database()
    ai = AIEngine(db)
    print("✅ AI Engine tayyor!")
    reply = ai.chat("Salom! Men B2 ga tayyorlanmoqchiman.")
    print("AI:", reply)
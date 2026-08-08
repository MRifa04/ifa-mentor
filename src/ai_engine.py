import json
import os
import requests
from config.settings import (
    AI_ENGINE,
    GEMINI_API_KEY, GEMINI_MODEL,
    ANTHROPIC_API_KEY,
    USER_NAME, CURRENT_SCORES,
    CEFR_LEVELS, READING_RULES
)

class AIEngine:
    def __init__(self, db):
        self.db = db
        self.conversation_history = []

        if AI_ENGINE == "gemini":
            self.api_key = GEMINI_API_KEY
            self.api_url = (
                f"https://generativelanguage.googleapis.com"
                f"/v1beta/models/{GEMINI_MODEL}"
                f":generateContent?key={self.api_key}"
            )

    # ─── ASOSIY YUBORISH ────────────────────────────────────

    def _send(self, system, user_msg, max_tokens=1000):
        if AI_ENGINE == "gemini":
            return self._send_gemini(system, user_msg)
        elif AI_ENGINE == "claude":
            return self._send_claude(system, user_msg, max_tokens)
        elif AI_ENGINE == "ollama":
            return self._send_ollama(system, user_msg)
        return "AI engine tanlanmagan"

    def _send_with_history(self, system, max_tokens=1000):
        if AI_ENGINE == "gemini":
            return self._send_gemini_with_history(system)
        elif AI_ENGINE == "claude":
            return self._send_claude_with_history(system, max_tokens)
        return "AI engine tanlanmagan"

    # ─── GEMINI ─────────────────────────────────────────────

    def _send_gemini(self, system, user_msg):
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"{system}\n\n{user_msg}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2000
                }
            }
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            data = response.json()
            print("DEBUG response:", json.dumps(data)[:300])

            if "error" in data:
                return f"Gemini xatosi: {data['error']['message']}"
            if "candidates" not in data:
                return f"Noto'g'ri response: {data}"

            return (
                data["candidates"][0]["content"]
                ["parts"][0]["text"]
            )
        except Exception as e:
            return f"Gemini xatosi: {e}"

    def _send_gemini_with_history(self, system):
        try:
            contents = []
            for msg in self.conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            if contents and contents[0]["role"] == "user":
                contents[0]["parts"][0]["text"] = (
                    f"{system}\n\n"
                    + contents[0]["parts"][0]["text"]
                )

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            data = response.json()

            if "error" in data:
                return f"Gemini xatosi: {data['error']['message']}"
            if "candidates" not in data:
                return f"Noto'g'ri response: {data}"

            reply = (
                data["candidates"][0]["content"]
                ["parts"][0]["text"]
            )
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })
            return reply
        except Exception as e:
            return f"Gemini xatosi: {e}"

    # ─── CLAUDE ─────────────────────────────────────────────

    def _send_claude(self, system, user_msg, max_tokens=1000):
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=ANTHROPIC_API_KEY
            )
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_msg}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Claude xatosi: {e}"

    def _send_claude_with_history(self, system, max_tokens):
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=ANTHROPIC_API_KEY
            )
            response = client.messages.create(
                model="claude-sonnet-4-6",
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
            return f"Claude xatosi: {e}"

    # ─── OLLAMA ─────────────────────────────────────────────

    def _send_ollama(self, system, user_msg):
        try:
            payload = {
                "model": "llama3",
                "prompt": f"{system}\n\n{user_msg}",
                "stream": False
            }
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            return response.json().get("response", "")
        except Exception as e:
            return f"Ollama xatosi: {e}"

    # ─── CHAT ───────────────────────────────────────────────

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

    def generate_reading_questions(self, text, part_name,
                                   level, question_type, count):
        system = """You are a CEFR exam question generator.
Generate exam questions exactly in JSON format. No extra text, only JSON."""

        prompt = f"""
Text: {text[:2000]}
Generate {count} {question_type} questions for {part_name} ({level} level).
Return ONLY valid JSON, no markdown, no backticks.
Format:
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
}}"""
        result = self._send(system, prompt, max_tokens=2000)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def evaluate_reading_answers(self, questions,
                                  user_answers, question_type):
        correct = 0
        total = len(questions)
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

        return {
            "correct": correct,
            "total": total,
            "percentage": round(
                (correct/total)*100, 1) if total > 0 else 0,
            "feedback": feedback
        }

    # ─── LISTENING ──────────────────────────────────────────

    def generate_listening_questions(self, transcript,
                                      part_name, level,
                                      question_type, count):
        system = """You are a CEFR Listening exam question generator.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Audio transcript: {transcript[:1500]}
Part: {part_name} | Level: {level} | Count: {count}

Generate {count} listening questions.
Return ONLY valid JSON:
{{
  "questions": [
    {{
      "id": 1,
      "question": "According to the speaker...?",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "explanation": "The speaker said..."
    }}
  ]
}}"""
        result = self._send(system, prompt, max_tokens=2000)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── WRITING ────────────────────────────────────────────

    def generate_writing_prompt(self, task_type, level="B2"):
        system = """You are a CEFR Writing examiner.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Generate a CEFR {level} {task_type} writing task.
Return ONLY valid JSON:
{{
  "task_type": "{task_type}",
  "level": "{level}",
  "topic": "...",
  "instructions": "Write a formal letter to...",
  "min_words": 150,
  "time_minutes": 30,
  "points_to_cover": ["point 1", "point 2", "point 3"]
}}"""
        result = self._send(system, prompt)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def evaluate_writing(self, task_type, prompt_text, user_essay):
        system = """You are an expert CEFR Writing examiner.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Task: {task_type}
Prompt: {prompt_text}
Essay: {user_essay}

Evaluate using CEFR rubric (0-5 each):
Return ONLY valid JSON:
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
  "strengths": ["..."],
  "improvements": ["..."],
  "corrected_sentences": [
    {{"original": "...", "corrected": "...", "reason": "..."}}
  ]
}}"""
        result = self._send(system, prompt, max_tokens=2000)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── SPEAKING ───────────────────────────────────────────

    def generate_speaking_questions(self, part_name, level, count):
        system = """You are a CEFR Speaking examiner.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Generate {count} speaking questions for {part_name} ({level}).
Return ONLY valid JSON:
{{
  "part": "{part_name}",
  "level": "{level}",
  "prep_time_seconds": 30,
  "questions": [
    {{
      "id": 1,
      "question": "Describe a place you visit often.",
      "type": "personal",
      "expected_duration_seconds": 60,
      "key_vocabulary": ["frequent", "atmosphere", "location"],
      "sample_answer_points": ["describe location", "why you go", "feelings"]
    }}
  ]
}}"""
        result = self._send(system, prompt)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def evaluate_speaking(self, question, transcript):
        system = """You are a CEFR Speaking examiner.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Question: {question}
Student answer: {transcript}

Evaluate (0-100 each):
Return ONLY valid JSON:
{{
  "scores": {{
    "Fluency": {{"score": 68, "feedback": "..."}},
    "Grammar": {{"score": 72, "feedback": "..."}},
    "Vocabulary": {{"score": 65, "feedback": "..."}},
    "Pronunciation": {{"score": 70, "feedback": "..."}}
  }},
  "overall": 68,
  "cefr_level": "B2",
  "strengths": ["..."],
  "improvements": ["..."],
  "better_phrases": [
    {{"original": "...", "better": "...", "context": "..."}}
  ],
  "ai_feedback": "..."
}}"""
        result = self._send(system, prompt, max_tokens=1500)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── VOCABULARY ─────────────────────────────────────────

    def analyze_vocabulary(self, text, source=""):
        system = """You are a vocabulary analyst for CEFR B2.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Text: {text[:2000]}
Extract 15 important B2-level words.
Return ONLY valid JSON:
{{
  "words": [
    {{
      "word": "sustainable",
      "uzbek": "barqaror",
      "pronunciation": "/səˈsteɪnəbl/",
      "definition": "able to continue over a long period",
      "example_from_text": "sustainable development",
      "ai_example": "We need sustainable solutions.",
      "level": "B2",
      "exam_frequency": "high"
    }}
  ]
}}"""
        result = self._send(system, prompt, max_tokens=3000)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    def generate_vocabulary_exercise(self, word, uzbek, example):
        system = """You are a vocabulary teacher.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Word: {word} | Uzbek: {uzbek} | Example: {example}
Return ONLY valid JSON:
{{
  "word": "{word}",
  "exercises": {{
    "gap_fill": {{
      "sentence": "The company uses ___ methods.",
      "answer": "{word}"
    }},
    "speaking_prompt": "Use '{word}' to describe your city.",
    "writing_prompt": "Write 2 sentences using '{word}'.",
    "synonyms": ["synonym1", "synonym2"],
    "antonyms": ["antonym1"]
  }}
}}"""
        result = self._send(system, prompt)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── DAILY PLAN ─────────────────────────────────────────

    def generate_daily_plan(self, weak_points, progress_history):
        system = """You are an AI study planner for CEFR B2.
Return ONLY valid JSON, no markdown, no backticks."""

        prompt = f"""
Student: {USER_NAME} | Level: B1 → B2 | Time: 90 min/day
Weak points: {json.dumps(weak_points[:5])}

Return ONLY valid JSON:
{{
  "focus_skill": "Speaking",
  "reason": "weakest skill",
  "tasks": [
    {{
      "order": 1,
      "skill": "Speaking",
      "task_type": "practice",
      "duration": 30,
      "description": "Part 2 practice",
      "priority": "high"
    }}
  ],
  "motivational_message": "You need only +5 to reach B2!"
}}"""
        result = self._send(system, prompt, max_tokens=1000)
        try:
            clean = result.strip().replace(
                "```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {"error": "JSON parse xatosi", "raw": result}

    # ─── CEFR CALCULATOR (Rule Engine) ──────────────────────

    def calculate_cefr_level(self, skill, part_results):
        b1_correct = b1_total = 0
        b2_correct = b2_total = 0
        c1_correct = c1_total = 0

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
                "B1": {"correct": b1_correct,
                       "total": b1_total,
                       "percentage": round(b1_pct, 1)},
                "B2": {"correct": b2_correct,
                       "total": b2_total,
                       "percentage": round(b2_pct, 1)},
                "C1": {"correct": c1_correct,
                       "total": c1_total,
                       "percentage": round(c1_pct, 1)}
            }
        }


# Test
if __name__ == "__main__":
    from src.database import Database
    db = Database()
    ai = AIEngine(db)
    print("✅ AI Engine tayyor!")
    result = ai._send(
        "You are helpful assistant",
        "Say hello in one sentence"
    )
    print("Gemini:", result)
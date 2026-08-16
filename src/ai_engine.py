import json
import requests

from config.settings import (
    AI_ENGINE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    ANTHROPIC_API_KEY,
    CEFR_LEVELS,
    READING_RULES,
)


from src.ai_skill_methods import AISkillMixin


class AIEngine(AISkillMixin):

    def __init__(self, db):
        self.db = db
        self.conversation_history = []

        from src.scores import get_current_scores
        from src.user_profile import get_profile

        self.user_name = get_profile(db)["name"]

        self.current_scores = get_current_scores(db)

        self.cefr_levels = CEFR_LEVELS

        # ==========================================
        # GEMINI
        # ==========================================

        self.api_key = GEMINI_API_KEY

        self.api_url = None

        if AI_ENGINE == "gemini":
            if not self.api_key:
                print(
                    "GEMINI_API_KEY topilmadi - AI ishlamaydi."
                )
            else:
                self.api_url = (
                    "https://generativelanguage.googleapis.com"
                    f"/v1beta/models/{GEMINI_MODEL}"
                    f":generateContent?key={self.api_key}"
                )

                print(
                    f"Gemini ulandi: {GEMINI_MODEL}"
                )

    def reload_profile(self, db):
        from src.scores import get_current_scores
        from src.user_profile import get_profile

        profile = get_profile(db)
        self.user_name = profile["name"]
        self.current_scores = get_current_scores(db)
        return profile

    # ==================================================
    # USER CONTEXT
    # ==================================================

    def get_user_context(self):

        scores = self.current_scores

        reading = scores.get(
            "reading",
            0,
        )

        listening = scores.get(
            "listening",
            0,
        )

        speaking = scores.get(
            "speaking",
            0,
        )

        writing = scores.get(
            "writing",
            0,
        )

        overall = scores.get(
            "overall",
            0,
        )

        skills = {
            "Reading": reading,
            "Listening": listening,
            "Speaking": speaking,
            "Writing": writing,
        }

        weakest_skill = min(
            skills,
            key=skills.get,
        )

        strongest_skill = max(
            skills,
            key=skills.get,
        )

        return {
            "name": self.user_name,
            "scores": scores,
            "overall": overall,
            "weakest_skill": weakest_skill,
            "strongest_skill": strongest_skill,
        }

    # ==================================================
    # SYSTEM PROMPT
    # ==================================================

    def build_system_prompt(self):

        context = self.get_user_context()

        return f"""
You are IFA Mentor, a personal AI learning mentor.

You are not a generic chatbot.

Your job is to understand the learner, remember
their progress, identify weaknesses and help them
improve step by step.

========================================
LEARNER PROFILE
========================================

Name:
{context["name"]}

Current overall score:
{context["overall"]}/75

Reading:
{context["scores"].get("reading", 0)}/75

Listening:
{context["scores"].get("listening", 0)}/75

Speaking:
{context["scores"].get("speaking", 0)}/75

Writing:
{context["scores"].get("writing", 0)}/75

Strongest skill:
{context["strongest_skill"]}

Weakest skill:
{context["weakest_skill"]}

========================================
MENTOR BEHAVIOR
========================================

1. Address the learner naturally by name when
   appropriate.

2. Give practical and personalized answers.

3. Consider the learner's CEFR/Multilevel goal
   when discussing English.

4. Pay special attention to the weakest skill.

5. Do not overwhelm the learner with unnecessary
   explanations.

6. If the learner asks an English-learning
   question, explain it clearly and give examples.

7. If the learner makes an English mistake,
   correct it politely.

8. When appropriate, suggest a concrete next action.

9. Never pretend to know something that is not
   available in the learner profile.

10. Do not claim that an estimated CEFR score is
    an official examination result.

========================================
LANGUAGE
========================================

The learner primarily communicates in Uzbek.

Use Uzbek by default.

English should be used when:
- teaching English;
- giving examples;
- practicing English;
- the learner explicitly requests English.

========================================
STYLE
========================================

Be concise, intelligent, supportive and direct.

Do not constantly repeat:
"Men IFA Mentor..."

Do not use excessive emojis.

Act like a serious personal mentor.
"""

    # ==================================================
    # MAIN SEND
    # ==================================================

    def _send(
        self,
        system,
        user_msg,
        max_tokens=1000,
    ):

        if AI_ENGINE == "gemini":
            if not self.api_key:
                return (
                    "Gemini API kaliti topilmadi. "
                    ".env faylida GEMINI_API_KEY ni kiriting."
                )

            return self._send_gemini(
                system,
                user_msg,
            )

        elif AI_ENGINE == "claude":

            return self._send_claude(
                system,
                user_msg,
                max_tokens,
            )

        elif AI_ENGINE == "ollama":

            return self._send_ollama(
                system,
                user_msg,
            )

        return "AI engine tanlanmagan."

    # ==================================================
    # GEMINI
    # ==================================================

    def _send_gemini(
        self,
        system,
        user_msg,
    ):

        try:

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text":
                                f"{system}\n\n"
                                f"USER:\n{user_msg}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2000,
                },
            }

            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type":
                    "application/json"
                },
                json=payload,
                timeout=60,
            )

            data = response.json()

            if "error" in data:

                return (
                    "Gemini xatosi: "
                    + data["error"].get(
                        "message",
                        "Noma'lum xato",
                    )
                )

            candidates = data.get(
                "candidates"
            )

            if not candidates:

                return (
                    "Gemini noto'g'ri response "
                    "qaytardi."
                )

            content = candidates[0].get(
                "content",
                {}
            )

            parts = content.get(
                "parts",
                []
            )

            if not parts:

                return (
                    "Gemini javob qaytarmadi."
                )

            return parts[0].get(
                "text",
                "Bo'sh javob.",
            )

        except requests.exceptions.Timeout:

            return (
                "Gemini javobi juda uzoq vaqt "
                "oldi. Internet aloqasini tekshiring."
            )

        except Exception as e:

            return (
                f"Gemini xatosi: {e}"
            )

    def generate_reply(
        self,
        system,
        user_message,
        max_tokens=1000,
    ):
        """Voice assistant va boshqa modullar uchun ochiq API."""
        from src.scores import get_current_scores

        self.current_scores = get_current_scores(self.db)
        return self._send(
            system,
            user_message,
            max_tokens=max_tokens,
        )

    # ==================================================
    # CHAT
    # ==================================================

    def chat(
        self,
        user_message,
    ):

        if not user_message.strip():

            return (
                "Savolingizni yozing."
            )

        from src.scores import get_current_scores

        self.current_scores = get_current_scores(
            self.db
        )

        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        system = self.build_system_prompt()

        prior_messages = self.conversation_history[:-1]
        recent_history = prior_messages[-10:]

        history_text = ""

        for message in recent_history:
            role = message["role"]
            content = message["content"]
            history_text += (
                f"{role.upper()}: {content}\n"
            )

        prompt = f"""
{system}

========================================
RECENT CONVERSATION
========================================

{history_text or "No prior messages."}

========================================
CURRENT USER MESSAGE
========================================

{user_message}

Answer the current user message.
"""

        response = self._send(
            system="",
            user_msg=prompt,
            max_tokens=1000,
        )

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        return response

    # ==================================================
    # CLAUDE
    # ==================================================

    def _send_claude(
        self,
        system,
        user_msg,
        max_tokens=1000,
    ):

        try:

            import anthropic

            client = anthropic.Anthropic(
                api_key=ANTHROPIC_API_KEY
            )

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[
                    {
                        "role": "user",
                        "content": user_msg,
                    }
                ],
            )

            return (
                response.content[0].text
            )

        except Exception as e:

            return (
                f"Claude xatosi: {e}"
            )

    # ==================================================
    # OLLAMA
    # ==================================================

    def _send_ollama(
        self,
        system,
        user_msg,
    ):

        try:

            payload = {
                "model": "llama3",
                "prompt":
                    f"{system}\n\n"
                    f"{user_msg}",
                "stream": False,
            }

            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60,
            )

            data = response.json()

            return data.get(
                "response",
                "",
            )

        except Exception as e:

            return (
                f"Ollama xatosi: {e}"
            )

    # ==================================================
    # RESET CHAT
    # ==================================================

    def reload_api_config(self):
        """API kalitlar .env dan qayta yuklanadi."""
        from dotenv import load_dotenv
        import importlib
        import config.settings as settings

        load_dotenv(override=True)
        importlib.reload(settings)
        self.api_key = settings.GEMINI_API_KEY
        if settings.AI_ENGINE == "gemini" and self.api_key:
            self.api_url = (
                "https://generativelanguage.googleapis.com"
                f"/v1beta/models/{settings.GEMINI_MODEL}"
                f":generateContent?key={self.api_key}"
            )
            print(f"Gemini qayta ulandi: {settings.GEMINI_MODEL}")
        else:
            self.api_url = None

    def clear_history(self):

        self.conversation_history = []

    # ==================================================
    # UPDATE SCORES
    # ==================================================

    def update_scores(
        self,
        scores,
    ):

        if not isinstance(
            scores,
            dict,
        ):
            return

        self.current_scores.update(
            scores
        )

    # ==================================================
    # MEMORY SUMMARY
    # ==================================================

    def get_memory_summary(self):

        context = (
            self.get_user_context()
        )

        return {
            "name":
                context["name"],

            "overall":
                context["overall"],

            "weakest_skill":
                context["weakest_skill"],

            "strongest_skill":
                context["strongest_skill"],

            "conversation_count":
                len(
                    self.conversation_history
                ),
        }
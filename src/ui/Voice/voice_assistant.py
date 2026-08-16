import threading
from datetime import datetime

from src.ui.Voice.speech import SpeechEngine


class VoiceAssistant:
    """
    IFA Mentor Voice Assistant.

    Vazifalari:
    - Foydalanuvchi buyruqlarini qabul qilish
    - AIEngine orqali javob olish
    - Dashboard va Smart Planner ma'lumotlaridan
      foydalanib kontekstli javob berish
    - Keyinchalik Speech-to-Text va Text-to-Speech
      bilan ulanish uchun tayyor arxitektura
    """

    def __init__(self, db, ai, user_name="Mr IFA"):
        self.db = db
        self.ai = ai
        self.user_name = user_name

        self.is_listening = False
        self.is_speaking = False
        self.is_processing = False

        self.on_state_changed = None
        self.on_response = None
        self.on_error = None

        self.speech = SpeechEngine()

    # =====================================================
    # STATE
    # =====================================================

    def _set_state(self, state):
        """
        State:
        idle
        listening
        thinking
        speaking
        error
        """

        if state == "listening":
            self.is_listening = True
            self.is_processing = False

        elif state == "thinking":
            self.is_listening = False
            self.is_processing = True

        elif state == "speaking":
            self.is_listening = False
            self.is_processing = False
            self.is_speaking = True

        else:
            self.is_listening = False
            self.is_processing = False
            self.is_speaking = False

        if self.on_state_changed:
            self.on_state_changed(state)

    # =====================================================
    # GREETING
    # =====================================================

    def get_greeting(self):
        hour = datetime.now().hour

        if hour < 12:
            greeting = "Xayrli tong"
        elif hour < 18:
            greeting = "Xayrli kun"
        else:
            greeting = "Xayrli kech"

        return (
            f"{greeting}, {self.user_name}! "
            f"Men IFA Mentor. Bugungi darslaringizga tayyorman."
        )

    # =====================================================
    # DASHBOARD CONTEXT
    # =====================================================

    def get_today_context(self):
        """
        Bugungi reja haqida ma'lumot yig'adi.
        """

        try:
            plan = self.db.get_today_plan()

            if not plan:
                return {
                    "tasks": [],
                    "completed": 0,
                    "remaining": 0,
                    "total_minutes": 0
                }

            completed = sum(
                1
                for task in plan
                if task.get("is_completed", 0)
            )

            total_minutes = sum(
                task.get("duration_minutes", 0)
                for task in plan
            )

            return {
                "tasks": plan,
                "completed": completed,
                "remaining": len(plan) - completed,
                "total_minutes": total_minutes
            }

        except Exception as e:
            print(f"IFA context xato: {e}")

            return {
                "tasks": [],
                "completed": 0,
                "remaining": 0,
                "total_minutes": 0
            }

    # =====================================================
    # TODAY'S MISSION
    # =====================================================

    def get_mission_summary(self):
        context = self.get_today_context()

        tasks = context["tasks"]

        if not tasks:
            return (
                "Bugun uchun hali dars rejasi topilmadi."
            )

        remaining_tasks = [
            task for task in tasks
            if not task.get("is_completed", 0)
        ]

        if not remaining_tasks:
            return (
                "Ajoyib! Bugungi barcha darslaringiz "
                "bajarilgan. Bugun uchun mission complete! 🎯"
            )

        lines = []

        for index, task in enumerate(
            remaining_tasks,
            start=1
        ):
            skill = task.get(
                "skill",
                "Unknown"
            )

            duration = task.get(
                "duration_minutes",
                0
            )

            task_type = task.get(
                "task_type",
                "practice"
            )

            task_type = (
                task_type
                .replace("_", " ")
                .title()
            )

            lines.append(
                f"{index}. {skill} — "
                f"{task_type}, {duration} daqiqa"
            )

        return (
            f"Bugun sizda {len(remaining_tasks)} ta "
            f"bajarilmagan vazifa bor.\n\n"
            + "\n".join(lines)
        )

    # =====================================================
    # AI RESPONSE
    # =====================================================

    def ask_ai(self, user_message):
        """
        Voice assistant uchun AIEngine bilan ishlaydi.
        """

        try:
            self._set_state("thinking")

            context = self.get_today_context()

            tasks_text = []

            for task in context["tasks"]:
                skill = task.get(
                    "skill",
                    "Unknown"
                )

                duration = task.get(
                    "duration_minutes",
                    0
                )

                completed = task.get(
                    "is_completed",
                    0
                )

                status = (
                    "bajarilgan"
                    if completed
                    else "bajarilmagan"
                )

                tasks_text.append(
                    f"{skill}: "
                    f"{duration} min, "
                    f"{status}"
                )

            context_text = (
                "\n".join(tasks_text)
                if tasks_text
                else "Bugungi reja mavjud emas."
            )

            system = f"""
You are IFA Mentor Voice Assistant.

User: {self.user_name}

Your role:
- Be a personal English learning assistant.
- Give short, natural spoken responses.
- Speak in the same language as the user.
- If the user speaks Uzbek, answer in Uzbek.
- Use the student's actual study plan when relevant.
- Never invent completed tasks or scores.
- Be encouraging but not childish.
- Keep voice responses concise.

Today's plan:
{context_text}

Current time:
{datetime.now().strftime("%H:%M")}
"""

            response = self.ai.generate_reply(
                system,
                user_message,
                max_tokens=500,
            )

            self._set_state("speaking")

            if response and self.speech.tts_available:
                self.speech.speak_async(response)

            if self.on_response:
                self.on_response(response)

            return response

        except Exception as e:

            self._set_state("error")

            message = (
                f"IFA Voice Assistant xatosi: {e}"
            )

            if self.on_error:
                self.on_error(message)

            return message

    # =====================================================
    # COMMAND PROCESSOR
    # =====================================================

    def process_command(self, command):
        """
        Ovozdan kelgan yoki UI orqali berilgan
        buyruqni qayta ishlaydi.
        """

        command = command.strip()

        if not command:
            return ""

        lower = command.lower()

        # ---------------------------------------------
        # GREETING
        # ---------------------------------------------

        if lower in [
            "salom",
            "hello",
            "hi",
            "hey",
            "salom ifa"
        ]:
            response = self.get_greeting()

            if self.on_response:
                self.on_response(response)

            return response

        # ---------------------------------------------
        # TODAY / MISSION
        # ---------------------------------------------

        if any(
            phrase in lower
            for phrase in [
                "bugun nima qilishim kerak",
                "bugungi darsim nima",
                "bugungi darslarim",
                "today's mission",
                "today mission"
            ]
        ):
            response = self.get_mission_summary()

            if self.on_response:
                self.on_response(response)

            return response

        # ---------------------------------------------
        # START STUDY
        # ---------------------------------------------

        if any(
            phrase in lower
            for phrase in [
                "darsni boshlaymiz",
                "darsni boshlash",
                "boshlaymiz",
                "let's study",
                "start lesson"
            ]
        ):
            response = (
                "Albatta. Tayyormiz. "
                "Bugungi birinchi vazifadan boshlaymiz."
            )

            if self.on_response:
                self.on_response(response)

            return response

        # ---------------------------------------------
        # REMAINING TASKS
        # ---------------------------------------------

        if any(
            phrase in lower
            for phrase in [
                "qancha darsim qoldi",
                "nechta dars qoldi",
                "nima qoldi",
                "remaining tasks"
            ]
        ):
            context = self.get_today_context()

            remaining = context["remaining"]

            response = (
                f"Bugun {remaining} ta "
                f"vazifangiz qoldi."
            )

            if self.on_response:
                self.on_response(response)

            return response

        # ---------------------------------------------
        # AI
        # ---------------------------------------------

        return self.ask_ai(command)

    def listen_and_process(self):
        """
        Mikrofondan eshitib, buyruqni qayta ishlaydi.
        Natijani on_response orqali qaytaradi.
        """

        def run():
            try:
                if not self.speech.stt_available:
                    message = (
                        "Mikrofon ishlamayapti. "
                        f"{self.speech.status_message()}"
                    )
                    if self.on_error:
                        self.on_error(message)
                    return

                self._set_state("listening")
                heard = self.speech.listen()

                if not heard:
                    message = (
                        "Eshitilmadi. Qaytadan urinib ko'ring."
                    )
                    if self.on_error:
                        self.on_error(message)
                    self._set_state("idle")
                    return

                response = self.process_command(heard)

                if self.on_response:
                    self.on_response(response)

                self._set_state("idle")

            except Exception as exc:
                self._set_state("error")
                if self.on_error:
                    self.on_error(str(exc))

        thread = threading.Thread(
            target=run,
            daemon=True,
        )
        thread.start()
        return thread

    def get_speech_status(self):
        return self.speech.status_message()

    # =====================================================
    # ASYNC COMMAND
    # =====================================================

    def process_async(self, command):
        """
        UI muzlab qolmasligi uchun buyruqni
        alohida thread'da bajaradi.
        """

        thread = threading.Thread(
            target=self.process_command,
            args=(command,),
            daemon=True
        )

        thread.start()

        return thread

    # =====================================================
    # LISTENING
    # =====================================================

    def start_listening(self):
        """
        Hozircha STT ulanmagan.
        Keyingi bosqichda mikrofon shu yerga ulanadi.
        """

        self._set_state("listening")

    def stop_listening(self):
        self._set_state("idle")

    # =====================================================
    # SPEAKING
    # =====================================================

    def start_speaking(self):
        self._set_state("speaking")

    def stop_speaking(self):
        self._set_state("idle")

    # =====================================================
    # RESET
    # =====================================================

    def reset(self):
        self.is_listening = False
        self.is_speaking = False
        self.is_processing = False

        self._set_state("idle")
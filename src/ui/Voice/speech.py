"""STT va TTS yordamchilari (ixtiyoriy — kutubxona bo'lmasa matn rejimi)."""

import threading


class SpeechEngine:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.stt_available = False
        self.tts_available = False
        self.last_error = ""
        self._init_engines()

    def _init_engines(self):
        try:
            import speech_recognition as sr

            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.4,
                )
            self.stt_available = True
        except Exception as exc:
            self.last_error = str(exc)
            self.stt_available = False

        try:
            import pyttsx3

            self.tts_engine = pyttsx3.init()
            self.tts_available = True
        except Exception as exc:
            if not self.last_error:
                self.last_error = str(exc)
            self.tts_available = False

    def listen(self, timeout=6, phrase_time_limit=12):
        if not self.stt_available:
            return None

        import speech_recognition as sr

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            text = self.recognizer.recognize_google(
                audio,
                language="uz-UZ",
            )

            if not text:
                text = self.recognizer.recognize_google(
                    audio,
                    language="en-US",
                )

            return text.strip() if text else None

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def speak(self, text):
        if not text or not self.tts_available:
            return

        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as exc:
            self.last_error = str(exc)

    def speak_async(self, text):
        threading.Thread(
            target=self.speak,
            args=(text,),
            daemon=True,
        ).start()

    def status_message(self):
        parts = []
        if self.stt_available:
            parts.append("mikrofon")
        if self.tts_available:
            parts.append("ovoz")
        if parts:
            return "Ovoz: " + ", ".join(parts)
        return (
            "Ovoz moduli ulanmagan "
            "(speech_recognition / pyttsx3 / pyaudio kerak)"
        )

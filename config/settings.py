import os
from dotenv import load_dotenv

load_dotenv()

# API Kalitlar
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")

# Foydalanuvchi
USER_NAME = "Ilhom"
CURRENT_LEVEL = "B1"
TARGET_LEVEL = "B2"
TARGET_DATE = "2026-10-01"

# Sertifikat ballari
CURRENT_SCORES = {
    "listening": 49,
    "reading": 55,
    "writing": 43,
    "speaking": 35,
    "vocabulary": 0,
    "overall": 46
}

# CEFR darajalar (TO'G'RI tizim)
CEFR_LEVELS = {
    "A1": (0, 25),
    "A2": (26, 40),
    "B1": (41, 50),
    "B2": (51, 64),
    "C1": (65, 75)
}

# B2 uchun maqsad (overall 51+)
TARGET_SCORES = {
    "overall": 51
}

# Rule Engine — Reading
READING_RULES = {
    "total_questions": 35,
    "parts": {
        "Part1": {"level": "B1", "questions": 5},
        "Part2": {"level": "B1", "questions": 5},
        "Part3": {"level": "B2", "questions": 7},
        "Part4": {"level": "B2", "questions": 6},
        "Part5": {"level": "C1", "questions": 6},
        "Part6": {"level": "C1", "questions": 6}
    }
}

# Papkalar
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
MATERIALS_DIR = r"D:\materials"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Kunlik o'qish vaqti (daqiqa)
DAILY_STUDY_TIME = 90

# Loyiha
APP_NAME = "IFA Mentor"
APP_TAGLINE = "A personal AI mentor that studies you before it teaches you."
APP_VERSION = "1.0.0"
# AI Engine tanlash
AI_ENGINE = "gemini"  # "gemini" | "claude" | "ollama"

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# Ollama (keyinroq)
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"
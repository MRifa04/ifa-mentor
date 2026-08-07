# IFA Mentor — Sozlamalar
import os
from dotenv import load_dotenv

load_dotenv()

# API Kalitlar
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Foydalanuvchi
USER_NAME = "Ilhom"
CURRENT_LEVEL = "B1"
TARGET_LEVEL = "B2"
TARGET_DATE = "2026-10-01"

# Ballar (sertifikatingizdan)
CURRENT_SCORES = {
    "listening": 49,
    "reading": 55,
    "writing": 43,
    "speaking": 35,
    "overall": 46
}

# Maqsad ballar (B2)
TARGET_SCORES = {
    "listening": 60,
    "reading": 60,
    "writing": 60,
    "speaking": 60,
    "overall": 51
}

# Papkalar
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Kunlik o'qish vaqti (daqiqa)
DAILY_STUDY_TIME = 90
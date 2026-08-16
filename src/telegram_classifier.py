"""Telegram postlarini skill, daraja va tur bo'yicha tasniflash."""

import os
import re

SKILLS = (
    "listening", "reading", "writing", "speaking",
    "vocabulary", "grammar", "tenses", "mock", "mixed",
)

SUPPORTED_AUDIO = {".mp3", ".ogg", ".wav", ".m4a", ".opus"}
SUPPORTED_DOC = {".pdf", ".txt", ".docx", ".doc"}
SUPPORTED_TEST = {".json"}

TENSE_KEYWORDS = {
    "present simple": "present_simple",
    "present continuous": "present_continuous",
    "past simple": "past_simple",
    "past continuous": "past_continuous",
    "present perfect": "present_perfect",
    "present perfect continuous": "present_perfect_continuous",
    "past perfect": "past_perfect",
    "past perfect continuous": "past_perfect_continuous",
    "future simple": "future_simple",
    "future continuous": "future_continuous",
    "future perfect": "future_perfect",
    "future perfect continuous": "future_perfect_continuous",
    "will": "future_simple",
    "going to": "future_simple",
}


def detect_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in SUPPORTED_AUDIO:
        return "audio"
    if ext == ".pdf":
        return "pdf"
    if ext in {".txt", ".doc", ".docx"}:
        return "txt"
    if ext in SUPPORTED_TEST:
        return "test"
    return "other"


def detect_level(filename: str = "", caption: str = "", text: str = "") -> str:
    blob = f"{filename} {caption} {text}".lower()
    for level in ("c1", "b2", "b1", "a2", "a1"):
        if level in blob:
            return level.upper()
    return "B2"


def detect_skill(
    filename: str = "",
    caption: str = "",
    text: str = "",
    default_skill: str = "mixed",
) -> str:
    blob = f"{filename} {caption} {text}".lower()

    if default_skill and default_skill not in ("mixed", ""):
        if default_skill in ("mock", "tenses", "grammar", "listening"):
            return default_skill

    rules = [
        ("mock", ["mock", "exam", "multilevel", "imtihon", "test paper", "practice test"]),
        ("tenses", ["tense", "zamon", "grammar tense", "present perfect", "past simple",
                    "future continuous", "past continuous", "present simple"]),
        ("grammar", ["grammar", "grammatika", "qoida", "rule", "modal", "passive",
                     "conditional", "article", "preposition"]),
        ("listening", ["listen", "audio", "bbc", "ielts audio", "listening", "podcast"]),
        ("reading", ["read", "reading", "text", "passage", "comprehension"]),
        ("writing", ["writ", "essay", "letter", "writing", "composition"]),
        ("speaking", ["speak", "speaking", "talk", "interview", "cue card"]),
        ("vocabulary", ["vocab", "word", "dictionary", "phrasal", "idiom"]),
    ]

    for skill, keywords in rules:
        if any(word in blob for word in keywords):
            return skill

    if default_skill and default_skill != "mixed":
        return default_skill
    return "mixed"


def detect_tense_tags(text: str) -> list[str]:
    """Matndan zamon teglarini chiqarish (tenses bo'limi uchun)."""
    blob = text.lower()
    tags = []
    for phrase, tag in TENSE_KEYWORDS.items():
        if phrase in blob:
            tags.append(tag)
    return list(dict.fromkeys(tags))


def classify_message(
    filename: str = "",
    caption: str = "",
    text: str = "",
    default_skill: str = "mixed",
    has_file: bool = True,
) -> dict:
    skill = detect_skill(filename, caption, text, default_skill)
    level = detect_level(filename, caption, text)
    tags = detect_tense_tags(f"{caption} {text}")

    if has_file and filename:
        file_type = detect_file_type(filename)
        category = "file"
    else:
        file_type = "text"
        category = "post"
        if skill in ("grammar", "tenses"):
            category = "grammar"

    title = filename or (text[:80] + "..." if len(text) > 80 else text) or "Telegram post"

    return {
        "skill": skill,
        "level": level,
        "file_type": file_type,
        "category": category,
        "tags": ",".join(tags),
        "title": title.strip(),
    }

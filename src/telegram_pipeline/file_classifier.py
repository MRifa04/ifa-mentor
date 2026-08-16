"""Fayl rollarini aniqlash: listening, reading, answers."""

import re
from dataclasses import dataclass
from typing import Optional

from src.telegram_grouping import (
    extract_day_number,
    extract_part_number,
    extract_test_number,
    is_announcement_post,
)
from src.telegram_pipeline.message_collector import RawMessage

ROLE_LISTENING = "listening"
ROLE_READING = "reading"
ROLE_ANSWERS = "answers"
ROLE_UNKNOWN = "unknown"

ANSWER_HINTS = (
    "answer", "answers", "javob", "javoblar", "key", "answer key",
    "correct", "solution",
)
READING_HINTS = (
    "mock", "multilevel", "day ", "reading", "exam", "test",
    "savol", "question",
)


@dataclass
class ClassifiedMessage:
    """Classifier chiqishi."""

    raw: RawMessage
    role: str
    part_order: int = 0
    day_number: int = 0
    test_number: int = 0
    includes_answers: bool = False
    confidence: float = 0.5
    notes: str = ""


class FileClassifier:
    """Mock kanal fayllarini Listening / Reading / Answers ga ajratadi."""

    def classify(self, msg: RawMessage) -> Optional[ClassifiedMessage]:
        if not msg.has_file:
            return None
        if msg.caption and is_announcement_post(msg.caption):
            return None

        blob = f"{msg.filename} {msg.caption}".lower()
        part = extract_part_number(msg.filename, msg.caption)
        day = extract_day_number(msg.filename, msg.caption)
        test_num = extract_test_number(msg.filename, msg.caption)

        if msg.file_type == "audio":
            return ClassifiedMessage(
                raw=msg,
                role=ROLE_LISTENING,
                part_order=part,
                day_number=day,
                test_number=test_num,
                confidence=0.9 if part else 0.6,
                notes="audio_part" if part else "audio_unnamed",
            )

        if msg.file_type == "pdf":
            has_answer_hint = any(h in blob for h in ANSWER_HINTS)
            has_reading_hint = any(h in blob for h in READING_HINTS)
            includes_answers = False

            if has_answer_hint and not has_reading_hint:
                role = ROLE_ANSWERS
                conf = 0.85
            else:
                role = ROLE_READING
                conf = 0.9 if day else 0.7
                includes_answers = True

            return ClassifiedMessage(
                raw=msg,
                role=role,
                day_number=day,
                test_number=test_num,
                includes_answers=includes_answers,
                confidence=conf,
                notes="pdf_exam" if role == ROLE_READING else "pdf_answers",
            )

        return ClassifiedMessage(
            raw=msg,
            role=ROLE_UNKNOWN,
            day_number=day,
            test_number=test_num,
            confidence=0.3,
            notes=msg.file_type,
        )

    def classify_batch(self, messages: list[RawMessage]) -> list[ClassifiedMessage]:
        result = []
        for msg in messages:
            item = self.classify(msg)
            if item:
                result.append(item)
        return result

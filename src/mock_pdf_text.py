"""Mock imtihon PDF dan listening/reading matnini ajratish."""

import re
from functools import lru_cache

from src.reading import ReadingModule


def _listening_section(pdf_text: str) -> str:
    start = pdf_text.find("PAPER 1")
    if start < 0:
        start = 0
    end = pdf_text.find("PAPER 2")
    if end < 0:
        end = len(pdf_text)
    return pdf_text[start:end]


def extract_listening_part_text(pdf_text: str, part_num: int) -> str:
    """PDF matnidan Listening Part N savollarini ajratadi."""
    if not pdf_text or part_num < 1 or part_num > 6:
        return ""

    section = _listening_section(pdf_text)
    matches = list(
        re.finditer(
            rf"(?:^|\n)Part {part_num}\s*\n",
            section,
            re.IGNORECASE,
        )
    )
    if not matches:
        return ""

    start = matches[-1].end()
    end = len(section)
    for next_part in range(part_num + 1, 7):
        next_matches = list(
            re.finditer(
                rf"(?:^|\n)Part {next_part}\s*\n",
                section[start:],
                re.IGNORECASE,
            )
        )
        if next_matches:
            end = start + next_matches[0].start()
            break

    return section[start:end].strip()


@lru_cache(maxsize=32)
def _cached_pdf_text(pdf_path: str) -> str:
    module = ReadingModule(db=None, ai_engine=None)
    return module.extract_text_from_pdf(pdf_path) or ""


def get_listening_part_from_pdf(pdf_path: str, part_num: int) -> str:
    if not pdf_path:
        return ""
    text = _cached_pdf_text(pdf_path)
    if not text:
        return ""
    return extract_listening_part_text(text, part_num)


def _paper_section(pdf_text: str, paper_num: int) -> str:
    markers = {
        1: "PAPER 1",
        2: "PAPER 2",
        3: "PAPER 3",
        4: "PAPER 4",
    }
    start_marker = markers.get(paper_num)
    if not start_marker:
        return ""

    start = pdf_text.find(start_marker)
    if start < 0:
        return ""

    end = len(pdf_text)
    for next_paper in range(paper_num + 1, 5):
        next_marker = markers.get(next_paper)
        if not next_marker:
            continue
        idx = pdf_text.find(next_marker, start + len(start_marker))
        if idx >= 0:
            end = idx
            break
    return pdf_text[start:end]


def extract_reading_part_text(pdf_text: str, part_num: int) -> str:
    if not pdf_text or part_num < 1 or part_num > 6:
        return ""

    section = _paper_section(pdf_text, 2)
    if not section:
        return ""

    matches = list(
        re.finditer(
            rf"(?:^|\n)Part {part_num}\s*\n",
            section,
            re.IGNORECASE,
        )
    )
    if not matches:
        return ""

    start = matches[-1].end()
    end = len(section)
    for next_part in range(part_num + 1, 7):
        next_matches = list(
            re.finditer(
                rf"(?:^|\n)Part {next_part}\s*\n",
                section[start:],
                re.IGNORECASE,
            )
        )
        if next_matches:
            end = start + next_matches[0].start()
            break
    return section[start:end].strip()


def get_reading_part_from_pdf(pdf_path: str, part_num: int) -> str:
    if not pdf_path:
        return ""
    text = _cached_pdf_text(pdf_path)
    if not text:
        return ""
    return extract_reading_part_text(text, part_num)


def get_writing_from_pdf(pdf_path: str) -> str:
    if not pdf_path:
        return ""
    text = _cached_pdf_text(pdf_path)
    if not text:
        return ""
    section = _paper_section(text, 3)
    return section.strip()


def get_speaking_from_pdf(pdf_path: str) -> str:
    if not pdf_path:
        return ""
    text = _cached_pdf_text(pdf_path)
    if not text:
        return ""
    section = _paper_section(text, 4)
    return section.strip()

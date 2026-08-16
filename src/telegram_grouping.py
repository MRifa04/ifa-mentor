"""Telegram postlarini mock imtihon to'plamlariga guruhlash.

Har bir mock = 1 PDF (savollar+javoblar) + 6 ta listening audio.
PDF va audiolar alohida post bo'ladi, lekin 1-3 daqiqa ichida chiqadi.
"""

import re
from collections import defaultdict
from datetime import datetime

PART_RE = re.compile(r"part\s*(\d+)", re.I)
DAY_RE = re.compile(r"day\s*(\d+)", re.I)
TEST_RE = re.compile(r"test\s*(\d+)", re.I)

AUDIO_EXT = (".mp3", ".ogg", ".m4a", ".wav", ".opus")

ANNOUNCEMENT_PATTERNS = [
    r"zoom",
    r"dars o['']?t",
    r"onlayn",
    r"telegram link",
    r"bog['']?lan",
    r"hamkor",
    r"qo['']?llanma",
    r"foydalaning",
    r"yoqdi",
    r"bugun \d{1,2}:\d{2}",
    r"live lesson",
    r"https?://t\.me/",
    r"https?://",
]

MOCK_PDF_GAP_SECONDS = 180


def extract_part_number(filename: str = "", title: str = "") -> int:
    blob = f"{filename} {title}"
    match = PART_RE.search(blob)
    return int(match.group(1)) if match else 0


def extract_day_number(*texts: str) -> int:
    for text in texts:
        if not text:
            continue
        match = DAY_RE.search(text)
        if match:
            return int(match.group(1))
    return 0


def extract_test_number(*texts: str) -> int:
    for text in texts:
        if not text:
            continue
        match = TEST_RE.search(text)
        if match:
            return int(match.group(1))
    return 0


def extract_day_from_set_title(title: str) -> int:
    return extract_day_number(title or "")


def is_announcement_post(text: str) -> bool:
    if not text or len(text.strip()) < 30:
        return True
    blob = text.lower().strip()
    hits = sum(1 for p in ANNOUNCEMENT_PATTERNS if re.search(p, blob))
    if hits >= 2:
        return True
    if hits == 1 and len(blob) < 120:
        return True
    if blob.startswith("http") and len(blob) < 200:
        return True
    return False


def safe_set_slug(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name or "channel")
    slug = re.sub(r"\s+", "_", slug.strip().lower())
    return slug[:60] or "channel"


def make_mock_set_id(channel_name: str, day: int) -> str:
    return f"{safe_set_slug(channel_name)}:day_{day}"


def make_mock_folder(day: int, fallback_id: int = 0) -> str:
    if day:
        return f"day_{day:03d}"
    return f"exam_{fallback_id}"


def _message_filename(msg) -> str:
    if msg.document:
        for attr in getattr(msg.document, "attributes", []) or []:
            name = getattr(attr, "file_name", None)
            if name:
                return name
    if msg.audio:
        return getattr(msg.audio, "title", None) or ""
    return ""


def _is_audio_filename(name: str) -> bool:
    return name.lower().endswith(AUDIO_EXT)


def _is_pdf_filename(name: str) -> bool:
    return name.lower().endswith(".pdf")


def _message_date(msg):
    return getattr(msg, "date", None)


def pair_mock_exams(messages, channel_name: str, max_gap_seconds: int = MOCK_PDF_GAP_SECONDS):
    """
    Mock kanal: har PDF ni eng yaqin audio albom bilan juftlash.
    Natija: [{messages, set_id, set_title, folder, day}, ...]
    """
    channel_slug = safe_set_slug(channel_name)
    pdfs = []
    albums_map = defaultdict(list)

    for msg in messages:
        fn = _message_filename(msg)
        if not fn:
            continue
        if _is_pdf_filename(fn):
            pdfs.append(msg)
        elif _is_audio_filename(fn) or msg.audio:
            gid = getattr(msg, "grouped_id", None) or f"audio_{msg.id}"
            albums_map[gid].append(msg)

    albums = []
    for gid, msgs in albums_map.items():
        dates = [d for d in (_message_date(m) for m in msgs) if d]
        albums.append({
            "messages": msgs,
            "date": min(dates) if dates else None,
            "matched": False,
            "parts": len(msgs),
        })

    albums.sort(key=lambda a: a["date"] or datetime.min, reverse=True)
    pdfs.sort(key=lambda m: _message_date(m) or datetime.min, reverse=True)

    exams = []
    for pdf_msg in pdfs:
        fn = _message_filename(pdf_msg)
        day = extract_day_number(fn, pdf_msg.message or "")
        pdf_date = _message_date(pdf_msg)

        best_album = None
        best_gap = max_gap_seconds + 1

        for album in albums:
            if album["matched"]:
                continue
            if not pdf_date or not album["date"]:
                continue
            gap = abs((pdf_date - album["date"]).total_seconds())
            if gap <= max_gap_seconds and album["parts"] >= 2 and gap < best_gap:
                best_gap = gap
                best_album = album

        if not best_album:
            continue

        best_album["matched"] = True
        set_id = make_mock_set_id(channel_name, day) if day else f"{channel_slug}:exam_{pdf_msg.id}"
        set_title = f"Mock Day {day}" if day else f"Mock Exam #{pdf_msg.id}"
        folder = make_mock_folder(day, pdf_msg.id)

        exams.append({
            "messages": [pdf_msg] + best_album["messages"],
            "set_id": set_id,
            "set_title": set_title,
            "folder": folder,
            "day": day,
            "channel_slug": channel_slug,
        })

    return exams


def cluster_messages(messages, window_seconds: int = 300):
    """Mock bo'lmagan kanallar uchun oddiy guruhlash."""
    if not messages:
        return []

    by_group = defaultdict(list)
    standalone = []
    for msg in messages:
        if getattr(msg, "grouped_id", None):
            by_group[msg.grouped_id].append(msg)
        else:
            standalone.append(msg)

    clusters = list(by_group.values())
    sorted_msgs = sorted(standalone, key=lambda m: _message_date(m) or datetime.min, reverse=True)

    if not sorted_msgs:
        return clusters

    current = [sorted_msgs[0]]
    for msg in sorted_msgs[1:]:
        anchor = current[0]
        a_date = _message_date(anchor)
        m_date = _message_date(msg)
        if a_date and m_date:
            delta = abs((a_date - m_date).total_seconds())
            if delta <= window_seconds:
                current.append(msg)
                continue
        clusters.append(current)
        current = [msg]
    clusters.append(current)
    return clusters


def build_set_info(messages, channel_name: str, default_skill: str = "mixed") -> dict:
    filenames = [_message_filename(m) for m in messages]
    filenames = [f for f in filenames if f]
    captions = [m.message for m in messages if m.message]
    blob = " ".join(filenames + captions)

    day = extract_day_number(blob, *captions)
    test_num = extract_test_number(blob, *captions)
    channel_slug = safe_set_slug(channel_name)

    if day:
        return {
            "set_id": make_mock_set_id(channel_name, day),
            "set_title": f"Mock Day {day}",
            "folder": make_mock_folder(day),
            "day": day,
            "channel_slug": channel_slug,
        }
    if test_num:
        return {
            "set_id": f"{channel_slug}:test_{test_num}",
            "set_title": f"Mock Test {test_num}",
            "folder": f"test_{test_num}",
            "day": 0,
            "channel_slug": channel_slug,
        }

    msg_id = min(m.id for m in messages)
    return {
        "set_id": f"{channel_slug}:msg_{msg_id}",
        "set_title": f"Set #{msg_id}",
        "folder": f"set_{msg_id}",
        "day": 0,
        "channel_slug": channel_slug,
    }


def parse_db_datetime(value: str):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def group_materials_for_library(materials: list) -> tuple:
    sets_map = defaultdict(lambda: {
        "title": "", "items": [], "skill": "mock", "level": "B2", "day": 0,
    })
    standalone = []

    for mat in materials:
        if mat.get("category") == "post" and mat.get("file_type") == "text":
            continue
        if mat.get("set_title") == "Listening Parts":
            continue

        set_id = mat.get("set_id") or ""
        if set_id.endswith("parts_pool"):
            continue

        if set_id:
            entry = sets_map[set_id]
            entry["title"] = mat.get("set_title") or set_id
            entry["skill"] = mat.get("skill", "mock")
            entry["level"] = mat.get("level", "B2")
            entry["day"] = extract_day_from_set_title(entry["title"])
            entry["items"].append(mat)
        elif mat.get("file_type") in ("pdf", "audio"):
            standalone.append(mat)

    for entry in sets_map.values():
        entry["items"].sort(
            key=lambda m: (
                0 if m.get("file_type") == "pdf" else 1,
                m.get("part_order") or extract_part_number(
                    m.get("title", ""), m.get("file_path", "")
                ) or 999,
            )
        )
        pdfs = sum(1 for m in entry["items"] if m.get("file_type") == "pdf")
        audios = sum(1 for m in entry["items"] if m.get("file_type") == "audio")
        entry["title"] = entry["title"] or "Mock"
        if entry["day"]:
            entry["title"] = f"Mock Day {entry['day']}"
        entry["summary"] = f"PDF {pdfs} + Audio {audios}"

    sets_list = sorted(
        sets_map.values(),
        key=lambda s: s.get("day", 0),
        reverse=True,
    )
    return sets_list, standalone

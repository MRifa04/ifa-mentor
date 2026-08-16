"""Mock to'plam validatsiyasi — PDF va audio mosligi."""

import os
from dataclasses import dataclass, field

from src.mock_pdf_text import (
    get_listening_part_from_pdf,
    get_reading_part_from_pdf,
    get_writing_from_pdf,
)

ROLE_ANSWERS = "answers"
EXPECTED_LISTENING_PARTS = 6


@dataclass
class ValidationResult:
    ok: bool
    score: float = 0.0
    issues: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def summary(self) -> str:
        if self.ok:
            return "Tayyor"
        return "; ".join(self.issues[:3])


def _is_answers_pdf(material: dict) -> bool:
    return (material.get("material_role") or "").lower() == ROLE_ANSWERS


def exam_pdf(materials: list[dict]) -> dict | None:
    """Javoblar PDF emas, asosiy imtihon PDF."""
    for material in materials:
        if material.get("file_type") == "pdf" and not _is_answers_pdf(material):
            return material
    for material in materials:
        if material.get("file_type") == "pdf":
            return material
    return None


def listening_audios(materials: list[dict]) -> list[dict]:
    items = [
        m for m in materials
        if m.get("file_type") == "audio"
    ]
    items.sort(key=lambda m: m.get("part_order") or 0)
    return items


def _audio_parts(audios: list[dict]) -> list[int]:
    parts = []
    for audio in audios:
        part = audio.get("part_order") or 0
        if part and part not in parts:
            parts.append(part)
    return sorted(parts)


def _file_exists(material: dict) -> bool:
    path = material.get("file_path", "")
    return bool(path and os.path.isfile(path))


def validate_listening(
    materials: list[dict],
    *,
    min_parts: int = 1,
    strict: bool = False,
) -> ValidationResult:
    issues: list[str] = []
    details: dict = {
        "audio_count": 0,
        "pdf_parts": [],
        "missing_audio_files": [],
        "duplicate_parts": [],
        "parts_without_pdf_text": [],
    }

    pdf = exam_pdf(materials)
    if not pdf:
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Imtihon PDF topilmadi"],
            details=details,
        )

    pdf_path = pdf.get("file_path", "")
    if not _file_exists(pdf):
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["PDF fayl diskda yo'q"],
            details=details,
        )

    audios = listening_audios(materials)
    details["audio_count"] = len(audios)
    if not audios:
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Listening audio topilmadi"],
            details=details,
        )

    seen_parts: dict[int, int] = {}
    for audio in audios:
        part = audio.get("part_order") or 0
        if not part:
            issues.append("Part raqamsiz audio mavjud")
            continue
        seen_parts[part] = seen_parts.get(part, 0) + 1
        if not _file_exists(audio):
            details["missing_audio_files"].append(part)

    details["duplicate_parts"] = [
        p for p, count in seen_parts.items() if count > 1
    ]
    if details["duplicate_parts"]:
        issues.append(
            "Takroriy audio part: "
            + ", ".join(str(p) for p in details["duplicate_parts"])
        )

    if details["missing_audio_files"]:
        issues.append(
            "Audio fayl yo'q: Part "
            + ", ".join(str(p) for p in details["missing_audio_files"])
        )

    parts = _audio_parts(audios)
    pdf_parts: list[int] = []
    for part in range(1, EXPECTED_LISTENING_PARTS + 1):
        text = get_listening_part_from_pdf(pdf_path, part)
        if text.strip():
            pdf_parts.append(part)
            if part in parts:
                details["pdf_parts"].append(part)
            elif strict:
                details["parts_without_pdf_text"].append(part)

    for part in parts:
        text = get_listening_part_from_pdf(pdf_path, part)
        if not text.strip():
            details["parts_without_pdf_text"].append(part)

    if details["parts_without_pdf_text"]:
        issues.append(
            "PDF da savol yo'q: Part "
            + ", ".join(str(p) for p in details["parts_without_pdf_text"])
        )

    if len(parts) < min_parts:
        issues.append(
            f"Kamida {min_parts} ta audio kerak (hozir {len(parts)})"
        )

    matched = len([
        p for p in parts
        if p in pdf_parts and p not in details["parts_without_pdf_text"]
    ])
    audio_score = min(len(parts), EXPECTED_LISTENING_PARTS) / EXPECTED_LISTENING_PARTS
    match_score = matched / max(len(parts), 1)
    file_score = 1.0 if not details["missing_audio_files"] else 0.0
    score = round((audio_score * 0.4 + match_score * 0.4 + file_score * 0.2), 2)

    ok = (
        not issues
        and len(parts) >= min_parts
        and matched == len(parts)
        and not details["missing_audio_files"]
    )
    return ValidationResult(ok=ok, score=score, issues=issues, details=details)


def validate_reading(materials: list[dict]) -> ValidationResult:
    issues: list[str] = []
    details: dict = {"pdf_parts": []}

    pdf = exam_pdf(materials)
    if not pdf:
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Reading uchun PDF topilmadi"],
            details=details,
        )

    pdf_path = pdf.get("file_path", "")
    if not _file_exists(pdf):
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["PDF fayl diskda yo'q"],
            details=details,
        )

    for part in range(1, 7):
        text = get_reading_part_from_pdf(pdf_path, part)
        if text.strip():
            details["pdf_parts"].append(part)

    if not details["pdf_parts"]:
        issues.append("PDF da Reading (PAPER 2) topilmadi")

    score = len(details["pdf_parts"]) / 6
    ok = bool(details["pdf_parts"])
    return ValidationResult(ok=ok, score=round(score, 2), issues=issues, details=details)


def validate_writing(materials: list[dict]) -> ValidationResult:
    pdf = exam_pdf(materials)
    if not pdf or not _file_exists(pdf):
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Writing uchun PDF topilmadi"],
        )

    text = get_writing_from_pdf(pdf.get("file_path", ""))
    if not text.strip():
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["PDF da Writing (PAPER 3) topilmadi"],
        )
    return ValidationResult(ok=True, score=1.0, details={"chars": len(text)})


def validate_for_skill(materials: list[dict], skill: str) -> ValidationResult:
    skill = (skill or "").strip().lower()
    if skill == "listening":
        return validate_listening(materials, min_parts=1)
    if skill == "reading":
        return validate_reading(materials)
    if skill == "writing":
        return validate_writing(materials)
    if skill == "speaking":
        pdf = exam_pdf(materials)
        if pdf and _file_exists(pdf):
            return ValidationResult(ok=True, score=0.8)
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Speaking uchun PDF topilmadi"],
        )
    return ValidationResult(ok=False, score=0.0, issues=["Noma'lum skill"])


def validate_mock_materials(
    materials: list[dict],
    *,
    strict_listening: bool = False,
) -> ValidationResult:
    """To'liq mock imtihon uchun PDF+audio mosligini tekshiradi."""
    if not materials:
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Material yo'q"],
        )

    listening = validate_listening(
        materials,
        min_parts=4 if not strict_listening else 6,
        strict=strict_listening,
    )
    reading = validate_reading(materials)

    issues = list(listening.issues) + list(reading.issues)
    score = round((listening.score * 0.6 + reading.score * 0.4), 2)
    ok = listening.ok and reading.ok

    if listening.details.get("audio_count", 0) < 4:
        issues.append(
            f"Listening: {listening.details.get('audio_count', 0)}/6 audio"
        )
        ok = False

    return ValidationResult(
        ok=ok,
        score=score,
        issues=issues,
        details={
            "listening": listening.details,
            "reading": reading.details,
        },
    )


def validate_mock_set(db, set_id: str) -> ValidationResult:
    """DB dan set_id bo'yicha validatsiya."""
    if not set_id:
        return ValidationResult(ok=False, score=0.0, issues=["set_id bo'sh"])
    materials = db.get_materials_by_set_id(set_id)
    return validate_mock_materials(materials)


def validate_mock_materials_quick(materials: list[dict]) -> ValidationResult:
    """PDF o'qimasdan tez tekshiruv — fayl soni va disk mavjudligi."""
    issues: list[str] = []
    details: dict = {
        "audio_count": 0,
        "pdf_count": 0,
        "missing_files": 0,
    }

    if not materials:
        return ValidationResult(
            ok=False,
            score=0.0,
            issues=["Material yo'q"],
            details=details,
        )

    pdf = exam_pdf(materials)
    all_pdfs = [m for m in materials if m.get("file_type") == "pdf"]
    audios = listening_audios(materials)
    details["audio_count"] = len(audios)
    details["pdf_count"] = len(all_pdfs)

    if not pdf:
        issues.append("Imtihon PDF yo'q")
    elif not _file_exists(pdf):
        issues.append("PDF diskda yo'q")
        details["missing_files"] += 1

    if not audios:
        issues.append("Audio yo'q")
        parts: list[int] = []
        dupes: list[int] = []
    else:
        parts = []
        for audio in audios:
            part = audio.get("part_order") or 0
            if part:
                parts.append(part)
            if not _file_exists(audio):
                details["missing_files"] += 1
                issues.append(f"Audio Part {part or '?'} diskda yo'q")

        dupes = [p for p in parts if parts.count(p) > 1]
        if dupes:
            issues.append(
                "Takroriy part: "
                + ", ".join(str(p) for p in sorted(set(dupes)))
            )

        if len(audios) < 4:
            issues.append(f"Kam audio: {len(audios)}/6")

        missing_parts = [
            p for p in range(1, 7)
            if p not in parts and len(audios) >= 4
        ]
        if missing_parts and len(audios) < 6:
            details["missing_audio_parts"] = missing_parts

    exam_status_issues = []
    if pdf and details["audio_count"] == 0:
        exam_status_issues.append("faqat PDF")
    if not pdf and details["audio_count"] > 0:
        exam_status_issues.append("faqat audio")
    if exam_status_issues:
        issues.append(" / ".join(exam_status_issues))

    unique_issues = []
    seen = set()
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            unique_issues.append(issue)

    audio_score = min(details["audio_count"], 6) / 6
    pdf_score = 1.0 if pdf and _file_exists(pdf) else 0.0
    file_score = 0.0 if details["missing_files"] else 1.0
    score = round(audio_score * 0.5 + pdf_score * 0.3 + file_score * 0.2, 2)

    ok = (
        pdf is not None
        and _file_exists(pdf)
        and details["audio_count"] >= 4
        and details["missing_files"] == 0
        and not dupes
    )

    return ValidationResult(
        ok=ok,
        score=score,
        issues=unique_issues,
        details=details,
    )


def validate_mock_set_quick(db, set_id: str) -> ValidationResult:
    if not set_id:
        return ValidationResult(ok=False, score=0.0, issues=["set_id bo'sh"])
    materials = db.get_materials_by_set_id(set_id)
    return validate_mock_materials_quick(materials)

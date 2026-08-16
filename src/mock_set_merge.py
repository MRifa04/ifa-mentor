"""Ajratilgan mock to'plamlarni birlashtirish (day_X + listening_day_X)."""

import re
from dataclasses import dataclass, field

from src.telegram_grouping import make_mock_set_id


LISTENING_DAY_RE = re.compile(r":listening_day_(\d+)$")
DAY_RE = re.compile(r":day_(\d+)$")


@dataclass
class MergeAction:
    source_set_id: str
    target_set_id: str
    channel_name: str
    day_number: int = 0
    moved_audio: int = 0
    moved_pdf: int = 0
    reason: str = ""


@dataclass
class MergeReport:
    merged: list[MergeAction] = field(default_factory=list)
    deleted_exams: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _count_types(materials: list[dict]) -> tuple[int, int]:
    audio = sum(1 for m in materials if m.get("file_type") == "audio")
    pdf = sum(
        1 for m in materials
        if m.get("file_type") == "pdf"
        and (m.get("material_role") or "").lower() != "answers"
    )
    return audio, pdf


def _day_from_set_id(set_id: str) -> int | None:
    for pattern in (LISTENING_DAY_RE, DAY_RE):
        match = pattern.search(set_id or "")
        if match:
            return int(match.group(1))
    return None


def _pick_primary(exams: list[dict], materials_by_set: dict) -> dict:
    """PDF bor va day_* formatidagi to'plamni tanlaydi."""
    def score(exam):
        sid = exam["set_id"]
        mats = materials_by_set.get(sid, [])
        audio, pdf = _count_types(mats)
        is_day = 1 if DAY_RE.search(sid) else 0
        is_listening = 1 if "listening" in sid else 0
        return (pdf, is_day, audio, -is_listening)

    return max(exams, key=score)


def plan_merges(db, channel_name: str | None = None) -> MergeReport:
    report = MergeReport()
    exams = db.get_mock_exams(channel_name)
    materials_by_set = {
        exam["set_id"]: db.get_materials_by_set_id(exam["set_id"])
        for exam in exams
    }

    groups: dict[tuple[str, int], list[dict]] = {}
    for exam in exams:
        day = exam.get("day_number") or _day_from_set_id(exam.get("set_id", ""))
        if not day:
            continue
        channel = exam.get("channel_name", "")
        groups.setdefault((channel, day), []).append(exam)

    for (channel, day), group in sorted(groups.items()):
        if len(group) < 2:
            continue

        primary = _pick_primary(group, materials_by_set)
        target_id = primary["set_id"]
        target_title = primary.get("set_title") or f"Mock Day {day}"

        for exam in group:
            source_id = exam["set_id"]
            if source_id == target_id:
                continue

            src_mats = materials_by_set.get(source_id, [])
            if not src_mats:
                report.skipped.append(f"{source_id}: bo'sh")
                continue

            src_audio, src_pdf = _count_types(src_mats)
            tgt_audio, tgt_pdf = _count_types(
                materials_by_set.get(target_id, [])
            )

            if src_audio == 0 and src_pdf == 0:
                continue

            if src_pdf > 0 and tgt_pdf > 0:
                report.skipped.append(
                    f"{source_id}: ikkala to'plamda PDF"
                )
                continue

            report.merged.append(MergeAction(
                source_set_id=source_id,
                target_set_id=target_id,
                channel_name=channel,
                day_number=day,
                moved_audio=src_audio,
                moved_pdf=src_pdf,
                reason=f"birlashtirildi -> {target_title}",
            ))

    return report


def apply_merges(db, report: MergeReport, dry_run: bool = False) -> MergeReport:
    if dry_run:
        return report

    for action in report.merged:
        target_exam = next(
            (
                e for e in db.get_mock_exams(action.channel_name)
                if e.get("set_id") == action.target_set_id
            ),
            None,
        )
        target_title = (
            target_exam.get("set_title", f"Mock Day {action.day_number}")
            if target_exam
            else f"Mock Day {action.day_number}"
        )

        for material in db.get_materials_by_set_id(action.source_set_id):
            db.update_material_set(
                material["id"],
                action.target_set_id,
                target_title,
                material.get("part_order") or 0,
            )

        db.delete_mock_exam(action.source_set_id)
        report.deleted_exams.append(action.source_set_id)
        refresh_mock_exam_counts(db, action.target_set_id)

    return report


def refresh_mock_exam_counts(db, set_id: str):
    materials = db.get_materials_by_set_id(set_id)
    if not materials:
        return

    first = materials[0]
    listening = sum(1 for m in materials if m.get("file_type") == "audio")
    reading = sum(
        1 for m in materials
        if m.get("file_type") == "pdf"
        and (m.get("material_role") or "").lower() != "answers"
    )
    answers = sum(
        1 for m in materials
        if m.get("file_type") == "pdf"
        and (m.get("material_role") or "").lower() == "answers"
    )

    day_number = 0
    match = re.search(r"Day\s+(\d+)", first.get("set_title", ""), re.I)
    if match:
        day_number = int(match.group(1))
    if not day_number:
        day_number = _day_from_set_id(set_id) or 0

    status = "auto_attached" if listening >= 4 and reading >= 1 else "review"
    confidence = 0.85 if status == "auto_attached" else 0.55

    db.upsert_mock_exam({
        "set_id": set_id,
        "set_title": first.get("set_title", set_id),
        "channel_name": first.get("source_channel", ""),
        "day_number": day_number,
        "confidence": confidence,
        "status": status,
        "listening_count": listening,
        "reading_count": reading,
        "answers_count": answers,
        "notes": "merged_sets",
    })


def merge_split_mock_sets(
    db,
    channel_name: str | None = None,
    dry_run: bool = False,
) -> MergeReport:
    report = plan_merges(db, channel_name)
    return apply_merges(db, report, dry_run=dry_run)

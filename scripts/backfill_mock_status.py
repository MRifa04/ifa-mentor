"""Eski sinxronlangan mock materiallarning resolve_status ni yangilash."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database


def backfill_channel(db, channel_name):
    exams = {
        e["set_id"]: e
        for e in db.get_mock_exams(channel_name)
    }
    materials = [
        m for m in db.get_all_materials()
        if m.get("source_channel") == channel_name
    ]
    if not materials:
        print(f"{channel_name}: material yo'q")
        return 0

    updated = 0
    with db.session() as conn:
        cursor = conn.cursor()
        by_set = {}
        for mat in materials:
            sid = mat.get("set_id") or ""
            by_set.setdefault(sid, []).append(mat)

        for set_id, items in by_set.items():
            if not set_id:
                continue
            exam = exams.get(set_id)
            aud = sum(1 for m in items if m.get("file_type") == "audio")
            pdf = sum(1 for m in items if m.get("file_type") == "pdf")

            if exam:
                status = exam.get("status", "review")
                confidence = exam.get("confidence", 0.75)
            elif aud >= 4 and pdf >= 1:
                status = "auto_attached"
                confidence = 0.8
            elif aud >= 2 or pdf >= 1:
                status = "review"
                confidence = 0.5
            else:
                continue

            for mat in items:
                if mat.get("resolve_status") == status:
                    continue
                role = mat.get("material_role") or ""
                if not role:
                    if mat.get("file_type") == "audio":
                        role = "listening"
                    elif mat.get("file_type") == "pdf":
                        role = "reading"
                cursor.execute(
                    """
                    UPDATE materials
                    SET resolve_status=?, resolve_confidence=?,
                        material_role=COALESCE(NULLIF(material_role,''), ?)
                    WHERE id=?
                    """,
                    (status, confidence, role, mat["id"]),
                )
                updated += 1

    pending = sum(
        1 for m in db.get_all_materials()
        if m.get("source_channel") == channel_name
        and m.get("resolve_status") == "pending"
    )
    print(f"{channel_name}: {updated} yangilandi, pending={pending}")
    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--channel",
        default="all",
        help="Multilevelzone Mock | Multilevel Halikulov | all",
    )
    args = parser.parse_args()

    db = Database()
    channels = [
        "Multilevelzone Mock",
        "Multilevel Halikulov",
    ]
    if args.channel != "all":
        channels = [args.channel]

    total = 0
    for ch in channels:
        total += backfill_channel(db, ch)
    print(f"Jami yangilandi: {total}")


if __name__ == "__main__":
    main()

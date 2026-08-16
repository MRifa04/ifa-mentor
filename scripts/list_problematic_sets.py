"""Muammoli mock to'plamlar ro'yxatini chiqarish."""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.mock_validation import validate_mock_set, validate_mock_set_quick

REPORT_DIR = Path(__file__).resolve().parents[1] / "database" / "reports"


def scan_exams(db, exams, deep: bool = False):
    rows = []
    for exam in exams:
        set_id = exam.get("set_id", "")
        if deep:
            result = validate_mock_set(db, set_id)
        else:
            result = validate_mock_set_quick(db, set_id)

        rows.append({
            "set_id": set_id,
            "title": exam.get("set_title", set_id),
            "channel": exam.get("channel_name", ""),
            "status": exam.get("status", ""),
            "day": exam.get("day_number") or 0,
            "audio": result.details.get("audio_count", 0),
            "pdf": result.details.get("pdf_count", 0),
            "score": result.score,
            "ok": result.ok,
            "issues": result.issues,
        })
    return rows


def build_report(rows, deep: bool) -> str:
    mode = "CHUQUR (PDF+audio)" if deep else "TEZ (fayl soni)"
    bad = [r for r in rows if not r["ok"]]
    ok_n = len(rows) - len(bad)

    lines = [
        f"Muammoli mock to'plamlar — {mode}",
        f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Jami: {len(rows)} | Tayyor: {ok_n} | Muammoli: {len(bad)}",
        "",
    ]

    by_channel = defaultdict(list)
    for row in bad:
        by_channel[row["channel"] or "Noma'lum"].append(row)

    for channel in sorted(by_channel.keys()):
        items = by_channel[channel]
        lines.append(f"=== {channel} ({len(items)} ta muammoli) ===")
        for row in sorted(items, key=lambda x: x["day"], reverse=True):
            issue_text = "; ".join(row["issues"]) if row["issues"] else "?"
            lines.append(f"  [{row['status']}] {row['title']}")
            lines.append(f"      set_id: {row['set_id']}")
            lines.append(
                f"      audio={row['audio']}, pdf={row['pdf']}, "
                f"score={row['score']:.2f}"
            )
            lines.append(f"      -> {issue_text}")
        lines.append("")

    if not bad:
        lines.append("Muammoli to'plam topilmadi.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Muammoli mock to'plamlar ro'yxati",
    )
    parser.add_argument("--channel", help="Faqat bitta kanal")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="PDF matnini ham tekshirish (sekin, ~1 soat)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="database/reports/ ga saqlash",
    )
    args = parser.parse_args()

    db = Database()
    exams = db.get_mock_exams()
    if args.channel:
        needle = args.channel.lower()
        exams = [
            e for e in exams
            if needle in (e.get("channel_name") or "").lower()
        ]

    print(f"Tekshirilmoqda: {len(exams)} ta to'plam...", flush=True)
    rows = scan_exams(db, exams, deep=args.deep)
    report = build_report(rows, deep=args.deep)
    print(report)

    if args.export:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        suffix = "deep" if args.deep else "quick"
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_path = REPORT_DIR / f"problematic_sets_{suffix}_{stamp}.txt"
        out_path.write_text(report, encoding="utf-8")
        print(f"\nSaqlandi: {out_path}", flush=True)


if __name__ == "__main__":
    main()

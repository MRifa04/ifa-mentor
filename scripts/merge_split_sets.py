"""Ajratilgan mock to'plamlarni birlashtirish."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.mock_set_merge import merge_split_mock_sets, plan_merges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", help="Faqat shu kanal")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Faqat reja, bazaga yozmaslik",
    )
    args = parser.parse_args()

    db = Database()
    if args.dry_run:
        report = plan_merges(db, args.channel)
        print(f"Birlashtirish rejasi: {len(report.merged)} ta\n")
        for action in report.merged:
            print(
                f"  {action.source_set_id}\n"
                f"    -> {action.target_set_id}\n"
                f"    audio={action.moved_audio}, pdf={action.moved_pdf}\n"
                f"    ({action.reason})"
            )
        if report.skipped:
            print(f"\nO'tkazib yuborilgan: {len(report.skipped)}")
            for line in report.skipped[:10]:
                print(f"  - {line}")
        return

    report = merge_split_mock_sets(db, args.channel, dry_run=False)
    print(f"Birlashtirildi: {len(report.merged)} ta")
    print(f"O'chirilgan mock_exam: {len(report.deleted_exams)}")
    for action in report.merged:
        print(f"  {action.source_set_id} -> {action.target_set_id}")


if __name__ == "__main__":
    main()

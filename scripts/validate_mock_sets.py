"""Barcha mock to'plamlarni validatsiya qilish."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.mock_validation import validate_mock_set


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    db = Database()
    exams = db.get_mock_exams()
    if args.limit:
        exams = exams[: args.limit]

    ok_count = 0
    fail_count = 0

    print(f"Mock imtihonlar: {len(exams)}\n", flush=True)
    for exam in exams:
        set_id = exam.get("set_id", "")
        title = exam.get("set_title", set_id)
        result = validate_mock_set(db, set_id)
        status = "OK" if result.ok else "FAIL"
        if result.ok:
            ok_count += 1
        else:
            fail_count += 1

        audio_n = result.details.get("listening", {}).get("audio_count", "?")
        print(
            f"[{status}] {title[:50]:50} "
            f"score={result.score:.2f} audio={audio_n}",
            flush=True,
        )
        if result.issues:
            print(f"       -> {result.summary()}", flush=True)

    print(
        f"\nNatija: {ok_count} tayyor, {fail_count} xato",
        flush=True,
    )


if __name__ == "__main__":
    main()

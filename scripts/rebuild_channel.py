"""Kanal materiallarini tozalab qayta sinxronlash.

Ishlatish:
  python scripts/rebuild_channel.py mock
  python scripts/rebuild_channel.py halikulov
  python scripts/rebuild_channel.py --list
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.telegram_channels import CHANNELS, channel_slug, get_channel_config
from src.telegram_loader import TelegramLoader

ALIASES = {
    "mock": "@Multilevelzone_mock",
    "multilevelzone": "@Multilevelzone_mock",
    "halikulov": "https://t.me/Multilevel_tushganlar",
    "tushganlar": "https://t.me/Multilevel_tushganlar",
}


def log(msg):
    print(msg, flush=True)


def find_channel(key: str) -> dict:
    raw = key.lower().strip()
    if raw in ALIASES:
        raw = ALIASES[raw]

    ch = get_channel_config(raw)
    if ch:
        return ch

    needle = channel_slug(raw)
    for alias, target in ALIASES.items():
        if needle == channel_slug(alias):
            ch = get_channel_config(target)
            if ch:
                return ch

    raise SystemExit(f"Kanal topilmadi: {key}")


def channel_stats(db, channel_name):
    materials = [
        m for m in db.get_all_materials()
        if m.get("source_channel") == channel_name
    ]
    sets = {m.get("set_id") for m in materials if m.get("set_id")}
    pdfs = sum(1 for m in materials if m.get("file_type") == "pdf")
    audios = sum(1 for m in materials if m.get("file_type") == "audio")
    pending = sum(
        1 for m in materials
        if m.get("resolve_status") == "pending"
    )
    return len(materials), len(sets), pdfs, audios, pending


def ensure_channel_row(db, ch):
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM telegram_channels
        WHERE channel_id=? OR channel_name=?
        """,
        (ch["channel_id"], ch["channel_name"]),
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            """
            UPDATE telegram_channels
            SET skill=?, channel_id=?, channel_name=?, is_active=1
            WHERE id=?
            """,
            (ch["skill"], ch["channel_id"], ch["channel_name"], row[0]),
        )
    else:
        cursor.execute(
            """
            INSERT INTO telegram_channels
            (channel_name, channel_id, skill, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (ch["channel_name"], ch["channel_id"], ch["skill"]),
        )
    conn.commit()
    db.close()


def validate(db, channel_name):
    exams = db.get_mock_exams(channel_name)
    log(f"\n=== TEKSHIRUV: {channel_name} ===")
    log(f"Mock to'plamlar: {len(exams)}")
    bad = []
    for exam in exams:
        set_id = exam["set_id"]
        mats = db.get_materials_by_set_id(set_id)
        aud = sum(1 for m in mats if m.get("file_type") == "audio")
        pdf = sum(1 for m in mats if m.get("file_type") == "pdf")
        if exam.get("listening_count", 0) and aud == 0:
            bad.append(f"{set_id}: audio yo'q")
        if exam.get("reading_count", 0) and pdf == 0:
            bad.append(f"{set_id}: pdf yo'q")
    orphans = [
        m for m in db.get_all_materials()
        if m.get("source_channel") == channel_name
        and not m.get("set_id")
    ]
    log(f"To'plamsiz materiallar: {len(orphans)}")
    if bad:
        log("Muammoli to'plamlar:")
        for line in bad[:10]:
            log(f"  - {line}")
    else:
        log("Juftlash xatolari topilmadi")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "channel",
        nargs="?",
        help="mock | halikulov | kanal nomi",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Mavjud kanallarni ko'rsatish",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Sinxronlashdan oldin bazadan o'chirish",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Faqat tekshirish, sinxronlamaslik",
    )
    args = parser.parse_args()

    if args.list or not args.channel:
        log("Mavjud kanallar:")
        for ch in CHANNELS:
            log(
                f"  {ch['label']}: {ch['channel_id']} "
                f"({ch['pipeline']}, skill={ch['skill']})"
            )
        return

    ch = find_channel(args.channel)
    db = Database()
    ensure_channel_row(db, ch)

    before = channel_stats(db, ch["channel_name"])
    log(
        f"Boshlang'ich [{ch['channel_name']}]: "
        f"{before[0]} fayl, {before[1]} to'plam, "
        f"PDF {before[2]}, Audio {before[3]}, "
        f"pending {before[4]}"
    )

    if args.validate_only:
        validate(db, ch["channel_name"])
        return

    if args.wipe:
        removed = db.clear_channel_materials(ch["channel_name"])
        log(f"O'chirildi: {removed} ta material (bazadan)")

    loader = TelegramLoader(db, on_progress=log)
    if not loader.is_ready():
        log(loader.status())
        sys.exit(1)

    limit = ch.get("sync_limit", 2500)
    log(f"\n=== {ch['channel_id']} — limit {limit} ===\n")
    log(
        "Eslatma: boshqa sync ishlamasin. IFA Mentor ochiq bo'lsa, "
        "avval yoping."
    )
    result = loader.sync_one(
        ch["channel_id"],
        ch["channel_name"],
        ch["skill"],
        limit=limit,
    )
    if result.get("error"):
        log(f"❌ {result['error']}")
        sys.exit(1)

    after = channel_stats(db, ch["channel_name"])
    log("\n=== NATIJA ===")
    log(str(result))
    log(
        f"Yakuniy: {after[0]} fayl, {after[1]} to'plam, "
        f"PDF {after[2]}, Audio {after[3]}, pending {after[4]}"
    )
    validate(db, ch["channel_name"])

    if ch.get("skill") == "mock":
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "backfill",
            os.path.join(ROOT, "scripts", "backfill_mock_status.py"),
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.backfill_channel(db, ch["channel_name"])


if __name__ == "__main__":
    main()

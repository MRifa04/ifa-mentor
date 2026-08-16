"""Multilevelzone_mock kanalidan barcha mocklarni yuklash (davom ettirish mumkin)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.telegram_loader import TelegramLoader

CHANNEL = "@Multilevelzone_mock"
CHANNEL_NAME = "Multilevelzone Mock"
LIMIT = 3500


def log(msg):
    print(msg, flush=True)


def stats(db):
    materials = db.get_all_materials()
    mock = [
        m for m in materials
        if m.get("source_channel") == CHANNEL_NAME
        or "multilevelzone" in (m.get("set_id") or "").lower()
    ]
    sets = {m.get("set_id") for m in mock if m.get("set_id")}
    pdfs = sum(1 for m in mock if m.get("file_type") == "pdf")
    audios = sum(1 for m in mock if m.get("file_type") == "audio")
    return len(mock), len(sets), pdfs, audios


def main():
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE telegram_channels
        SET skill='mock', channel_id=?
        WHERE channel_id LIKE '%Multilevelzone_mock%'
           OR channel_name = 'Multilevelzone Mock'
        """,
        (CHANNEL,),
    )
    conn.commit()
    db.close()

    before = stats(db)
    log(f"Boshlang'ich: {before[0]} fayl, {before[1]} to'plam, PDF {before[2]}, Audio {before[3]}")

    loader = TelegramLoader(db, on_progress=log)
    if not loader.is_ready():
        log(loader.status())
        sys.exit(1)

    log(f"\n=== {CHANNEL} — limit {LIMIT} ===\n")
    result = loader.sync_one(CHANNEL, CHANNEL_NAME, "mock", limit=LIMIT)

    after = stats(db)

    log("\n=== NATIJA ===")
    log(str(result))
    log(
        f"Yakuniy: {after[0]} fayl, {after[1]} to'plam, "
        f"PDF {after[2]}, Audio {after[3]}"
    )
    log(f"Yangi: +{after[0]-before[0]} fayl, +{after[1]-before[1]} to'plam")


if __name__ == "__main__":
    main()

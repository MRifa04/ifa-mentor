"""Telegram kanallarini IFA Mentor kutubxonasiga ulash."""

import asyncio
import os
import shutil
import threading
from typing import Callable, Optional

from config.settings import MATERIALS_DIR
from src.telegram_classifier import detect_file_type, detect_skill, detect_level
from src.telegram_sync import TelegramSyncEngine

_sync_lock = threading.Lock()


class TelegramLoader:
  """Kanal sinxronlash va qo'lda material qo'shish."""

  def __init__(self, db, on_progress: Optional[Callable[[str], None]] = None):
    self.db = db
    self.on_progress = on_progress or (lambda _msg: None)
    self.download_dir = MATERIALS_DIR
    self.engine = TelegramSyncEngine(db, on_progress=on_progress)
    os.makedirs(self.download_dir, exist_ok=True)

  def status(self) -> str:
    return self.engine.status_message()

  def is_ready(self) -> bool:
    return self.engine.is_configured() and self.engine.session_exists()

  # ─── KANAL ───────────────────────────────────────────────

  def add_channel(self, channel_name, channel_id, skill):
    self.db.add_channel(channel_name, channel_id, skill)
    self.on_progress(f"✅ Kanal qo'shildi: {channel_name} → {skill}")

  def detect_file_type(self, filename):
    return detect_file_type(filename)

  def detect_skill(self, filename, caption="", default_skill="mixed"):
    return detect_skill(filename, caption, default_skill=default_skill)

  def detect_level(self, filename, caption=""):
    return detect_level(filename, caption)

  # ─── SINXRONLASH ─────────────────────────────────────────

  async def sync_channel(self, channel_id, channel_name, skill, limit=100):
    return await self.engine.sync_channel(
      channel_id or channel_name,
      channel_name,
      skill,
      limit=limit,
    )

  async def sync_all_channels(self, limit_per_channel=100):
    return await self.engine.sync_all_channels(limit_per_channel=limit_per_channel)

  def sync(self, limit_per_channel=100):
    if not _sync_lock.acquire(blocking=False):
      raise RuntimeError(
        "Sinxronlash allaqachon davom etmoqda. Tugashini kuting."
      )
    try:
      return asyncio.run(self.sync_all_channels(limit_per_channel))
    finally:
      _sync_lock.release()

  def sync_one(self, channel_id, channel_name, skill, limit=100):
    return asyncio.run(self.sync_channel(channel_id, channel_name, skill, limit))

  # ─── STATISTIKA ──────────────────────────────────────────

  def get_stats(self):
    conn = self.db.connect()
    cursor = conn.cursor()
    cursor.execute("""
      SELECT skill, file_type, COUNT(*) as count
      FROM materials
      GROUP BY skill, file_type
      ORDER BY skill
    """)
    rows = cursor.fetchall()
    self.db.close()

    print("\n📊 Material statistikasi:")
    print("─" * 40)
    current_skill = None
    for row in rows:
      if row["skill"] != current_skill:
        current_skill = row["skill"]
        print(f"\n📁 {current_skill.upper()}")
      print(f"   {row['file_type']:10} → {row['count']} ta")
    print("─" * 40)
    return [dict(r) for r in rows]

  # ─── QO'LDA QO'SHISH ─────────────────────────────────────

  def add_manual_material(self, file_path, skill, level="B2"):
    if not os.path.exists(file_path):
      self.on_progress(f"❌ Fayl topilmadi: {file_path}")
      return False

    filename = os.path.basename(file_path)
    file_type = self.detect_file_type(filename)
    skill_dir = os.path.join(self.download_dir, skill)
    os.makedirs(skill_dir, exist_ok=True)
    dest = os.path.join(skill_dir, filename)

    if not os.path.exists(dest):
      shutil.copy2(file_path, dest)

    self.db.add_material(
      title=filename,
      file_path=dest,
      file_type=file_type,
      skill=skill,
      level=level,
      channel="manual",
      msg_id=0,
      category="file",
    )
    self.on_progress(f"✅ Qo'shildi: {filename} → {skill}")
    return True


if __name__ == "__main__":
  from src.database import Database

  db = Database()
  loader = TelegramLoader(db)
  print(loader.status())
  loader.get_stats()

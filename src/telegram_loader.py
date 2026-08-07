import os
import asyncio
import json
import re
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from config.settings import TELEGRAM_BOT_TOKEN, DATABASE_DIR

class TelegramLoader:
    def __init__(self, db):
        self.db = db
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.download_dir = DATABASE_DIR
        self.supported_types = {
            "audio": [".mp3", ".ogg", ".wav", ".m4a"],
            "document": [".pdf", ".txt", ".docx"],
            "test": [".json"],
        }

    # ─── KANAL QOSHISH ──────────────────────────────────────

    def add_channel(self, channel_name, channel_id, skill):
        """
        Yangi telegram kanal qo'shish
        channel_name: @multilevel_english
        channel_id:   -1001234567890
        skill:        listening | reading | writing | speaking | mixed
        """
        self.db.add_channel(channel_name, channel_id, skill)
        print(f"✅ Kanal qo'shildi: {channel_name} → {skill}")

    # ─── FAYL TURINI ANIQLASH ───────────────────────────────

    def detect_file_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.supported_types["audio"]:
            return "audio"
        elif ext in [".pdf"]:
            return "pdf"
        elif ext in [".txt"]:
            return "txt"
        elif ext in [".json"]:
            return "test"
        else:
            return "other"

    def detect_skill(self, filename, caption=""):
        """
        Fayl nomi yoki caption dan skill aniqlash
        """
        text = (filename + " " + caption).lower()
        if any(w in text for w in ["listen", "audio", "bbc", "ielts_audio", "listening"]):
            return "listening"
        elif any(w in text for w in ["read", "reading", "text", "passage"]):
            return "reading"
        elif any(w in text for w in ["writ", "essay", "letter", "writing"]):
            return "writing"
        elif any(w in text for w in ["speak", "speaking", "talk"]):
            return "speaking"
        elif any(w in text for w in ["vocab", "word", "dictionary"]):
            return "vocabulary"
        elif any(w in text for w in ["test", "mock", "exam", "multilevel"]):
            return "mixed"
        else:
            return "mixed"

    def detect_level(self, filename, caption=""):
        text = (filename + " " + caption).lower()
        if "c1" in text:
            return "C1"
        elif "b2" in text:
            return "B2"
        elif "b1" in text:
            return "B1"
        else:
            return "B2"

    # ─── FAYL YUKLASH ───────────────────────────────────────

    async def download_file(self, file_id, filename, skill):
        """
        Telegram dan fayl yuklab olish
        """
        try:
            skill_dir = os.path.join(self.download_dir, skill)
            os.makedirs(skill_dir, exist_ok=True)
            save_path = os.path.join(skill_dir, filename)

            if os.path.exists(save_path):
                print(f"⏭️  Allaqachon bor: {filename}")
                return save_path

            file = await self.bot.get_file(file_id)
            await file.download_to_drive(save_path)
            print(f"✅ Yuklandi: {filename}")
            return save_path

        except TelegramError as e:
            print(f"❌ Yuklash xatosi: {e}")
            return None

    # ─── KANALDAN MATERIALLAR OLISH ─────────────────────────

    async def sync_channel(self, channel_id, channel_name, skill, limit=50):
        """
        Kanaldan oxirgi materiallarni yuklab olish
        """
        print(f"\n📡 Sinxronlash: {channel_name}")
        downloaded = 0
        skipped = 0

        try:
            updates = await self.bot.get_updates(limit=100)

            # Kanal xabarlarini olish
            async for message in self._get_channel_messages(channel_id, limit):
                filename = None
                file_id = None
                caption = message.caption or ""

                # Audio fayl
                if message.audio:
                    file_id = message.audio.file_id
                    filename = message.audio.file_name or f"audio_{message.message_id}.mp3"

                # Hujjat (PDF, TXT)
                elif message.document:
                    file_id = message.document.file_id
                    filename = message.document.file_name or f"doc_{message.message_id}.pdf"

                # Video nota (audio sifatida)
                elif message.voice:
                    file_id = message.voice.file_id
                    filename = f"voice_{message.message_id}.ogg"

                if file_id and filename:
                    file_type = self.detect_file_type(filename)
                    detected_skill = self.detect_skill(filename, caption) if skill == "mixed" else skill
                    detected_level = self.detect_level(filename, caption)

                    if file_type == "other":
                        skipped += 1
                        continue

                    save_path = await self.download_file(file_id, filename, detected_skill)

                    if save_path:
                        self.db.add_material(
                            title=filename,
                            file_path=save_path,
                            file_type=file_type,
                            skill=detected_skill,
                            level=detected_level,
                            channel=channel_name,
                            msg_id=message.message_id
                        )
                        downloaded += 1

        except Exception as e:
            print(f"❌ Kanal xatosi {channel_name}: {e}")

        print(f"✅ {channel_name}: {downloaded} ta yuklandi, {skipped} ta o'tkazildi")
        return downloaded

    async def _get_channel_messages(self, channel_id, limit=50):
        """
        Kanal xabarlarini generator sifatida qaytarish
        """
        try:
            # Telegram Bot API orqali forward qilingan xabarlarni olish
            messages = []
            offset = 0

            while len(messages) < limit:
                updates = await self.bot.get_updates(
                    offset=offset,
                    limit=min(100, limit - len(messages)),
                    allowed_updates=["channel_post"]
                )
                if not updates:
                    break
                for update in updates:
                    if update.channel_post:
                        msg = update.channel_post
                        if str(msg.chat.id) == str(channel_id):
                            messages.append(msg)
                    offset = update.update_id + 1

            for msg in messages:
                yield msg

        except Exception as e:
            print(f"❌ Xabarlar olishda xato: {e}")

    # ─── BARCHA KANALLARNI SINXRONLASH ──────────────────────

    async def sync_all_channels(self):
        """
        Bazadagi barcha aktiv kanallarni sinxronlash
        """
        channels = self.db.get_active_channels()
        if not channels:
            print("⚠️  Hech qanday kanal qo'shilmagan!")
            print("Kanal qo'shish uchun: loader.add_channel('@kanal_nomi', 'kanal_id', 'skill')")
            return

        print(f"\n🔄 {len(channels)} ta kanal sinxronlanmoqda...")
        total = 0
        for ch in channels:
            count = await self.sync_channel(
                ch["channel_id"],
                ch["channel_name"],
                ch["skill"]
            )
            total += count
            # Kanal oxirgi sinxronlanish vaqtini yangilash
            self.db.connect().execute(
                "UPDATE telegram_channels SET last_sync=?, total_materials=total_materials+? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), count, ch["id"])
            )

        print(f"\n✅ Jami {total} ta material yuklandi!")
        return total

    # ─── SINXRON WRAPPER ────────────────────────────────────

    def sync(self):
        """Async ni sync ga o'tkazish"""
        return asyncio.run(self.sync_all_channels())

    def sync_one(self, channel_id, channel_name, skill):
        """Bitta kanalni sinxronlash"""
        return asyncio.run(self.sync_channel(channel_id, channel_name, skill))

    # ─── MATERIALLAR STATISTIKASI ────────────────────────────

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

    # ─── MANUAL MATERIAL QOSHISH ────────────────────────────

    def add_manual_material(self, file_path, skill, level="B2"):
        """
        Telegram dan emas, qo'lda fayl qo'shish
        """
        if not os.path.exists(file_path):
            print(f"❌ Fayl topilmadi: {file_path}")
            return False

        filename = os.path.basename(file_path)
        file_type = self.detect_file_type(filename)

        # Fayl ni database papkasiga ko'chirish
        skill_dir = os.path.join(self.download_dir, skill)
        os.makedirs(skill_dir, exist_ok=True)
        dest = os.path.join(skill_dir, filename)

        if not os.path.exists(dest):
            import shutil
            shutil.copy2(file_path, dest)

        self.db.add_material(
            title=filename,
            file_path=dest,
            file_type=file_type,
            skill=skill,
            level=level,
            channel="manual",
            msg_id=0
        )
        print(f"✅ Qo'shildi: {filename} → {skill}")
        return True


# Test
if __name__ == "__main__":
    from src.database import Database
    db = Database()
    loader = TelegramLoader(db)

    # Kanal qo'shish misoli
    # loader.add_channel("@multilevel_english", "-1001234567890", "mixed")
    # loader.add_channel("@british_council_audio", "-1009876543210", "listening")

    # Statistika
    loader.get_stats()

    print("\n✅ Telegram Loader tayyor!")
    print("Kanal qo'shish uchun:")
    print('loader.add_channel("@kanal_nomi", "kanal_id", "skill")')
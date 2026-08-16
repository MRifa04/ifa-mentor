"""Telegram sessiyasini bir marta yaratish (Telethon).

Ishlatish:
    python -m src.telegram_auth

my.telegram.org dan API_ID va API_HASH oling,
.env fayliga qo'shing, keyin shu skriptni ishga tushiring.
"""

import asyncio
import os
import sys

from config.settings import DATABASE_DIR, TELEGRAM_API_HASH, TELEGRAM_API_ID

SESSION_PATH = os.path.join(DATABASE_DIR, "telegram")


async def main():
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ TELEGRAM_API_ID va TELEGRAM_API_HASH .env da kerak")
        print("   https://my.telegram.org → API development tools")
        sys.exit(1)

    try:
        from telethon import TelegramClient
    except ImportError:
        print("❌ telethon o'rnatilmagan: pip install telethon")
        sys.exit(1)

    os.makedirs(DATABASE_DIR, exist_ok=True)
    client = TelegramClient(
        SESSION_PATH,
        int(TELEGRAM_API_ID),
        TELEGRAM_API_HASH,
    )

    print("IFA Mentor — Telegram kirish")
    print("Telefon raqamingiz va kod so'raladi (bir marta).")
    await client.start()
    me = await client.get_me()
    name = me.first_name or me.username or "user"
    print(f"\n✅ Muvaffaqiyatli: {name}")
    print(f"   Sessiya: {SESSION_PATH}.session")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

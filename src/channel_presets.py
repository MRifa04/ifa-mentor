"""CEFR kanallar uchun tayyor shablonlar.

Kanal ID ni bilmasangiz, faqat @username yetarli (Telethon).
"""

from src.telegram_channels import CHANNELS

CHANNEL_PRESETS = [
    {
        "label": ch["label"],
        "channel_name": ch["channel_name"],
        "channel_id": ch["channel_id"],
        "skill": ch["skill"],
    }
    for ch in CHANNELS
]
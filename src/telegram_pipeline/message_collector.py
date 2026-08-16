"""Telegram xabarlarini yig'ish (Message Collector)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class RawMessage:
    """Telegram postini pipeline uchun normalizatsiya qilish."""

    message_id: int
    channel_name: str
    filename: str
    file_type: str
    caption: str
    grouped_id: Optional[int]
    date: Optional[datetime]
    has_file: bool
    raw: Any = field(repr=False, default=None)

    @property
    def date_iso(self) -> str:
        if self.date:
            return self.date.strftime("%Y-%m-%d %H:%M:%S")
        return ""


def message_filename(message) -> str:
    if message.document:
        for attr in getattr(message.document, "attributes", []) or []:
            name = getattr(attr, "file_name", None)
            if name:
                return name
        mime = getattr(message.document, "mime_type", "") or ""
        ext = ".pdf" if "pdf" in mime else ".bin"
        return f"doc_{message.id}{ext}"
    if message.audio:
        title = getattr(message.audio, "title", None)
        if title:
            return title
        return f"audio_{message.id}.mp3"
    if message.voice:
        return f"voice_{message.id}.ogg"
    return ""


def message_has_file(message) -> bool:
    return bool(message.document or message.audio or message.voice)


class MessageCollector:
    """Kanaldan fayl-postlarni yig'adi."""

    def collect_from_iter(self, messages_iter, channel_name: str) -> list[RawMessage]:
        from src.telegram_classifier import detect_file_type

        items = []
        for message in messages_iter:
            if not message_has_file(message):
                continue
            filename = message_filename(message)
            if detect_file_type(filename) == "other":
                continue
            items.append(
                RawMessage(
                    message_id=message.id,
                    channel_name=channel_name,
                    filename=filename,
                    file_type=detect_file_type(filename),
                    caption=(message.message or "").strip(),
                    grouped_id=getattr(message, "grouped_id", None),
                    date=getattr(message, "date", None),
                    has_file=True,
                    raw=message,
                )
            )
        return items

    async def collect_channel(
        self,
        client,
        entity,
        channel_name: str,
        limit: int = 2500,
    ) -> list[RawMessage]:
        messages = []
        async for message in client.iter_messages(entity, limit=limit):
            messages.append(message)
        return self.collect_from_iter(messages, channel_name)

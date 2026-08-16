"""Telethon orqali Telegram kanal tarixini o'qish va bazaga yozish."""

import os
import re
import sqlite3
from datetime import datetime
from typing import Callable, Optional

from config.settings import DATABASE_DIR, MATERIALS_DIR
from src.telegram_classifier import classify_message, detect_file_type
from src.telegram_grouping import (
    build_set_info,
    cluster_messages,
    extract_part_number,
    safe_set_slug,
)
from src.telegram_pipeline import MockPipeline
from src.telegram_pipeline.mock_resolver import MockBundle

SESSION_PATH = os.path.join(DATABASE_DIR, "telegram")
MOCK_SYNC_LIMIT = 2500


def _telegram_credentials():
    from dotenv import load_dotenv
    load_dotenv(override=True)
    api_id = os.getenv("TELEGRAM_API_ID", "")
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    return api_id, api_hash


class TelegramSyncEngine:
    """Mock kanal: har PDF + 6 audio = 1 imtihon, kanal papkasida."""

    def __init__(self, db, on_progress: Optional[Callable[[str], None]] = None):
        self.db = db
        self.on_progress = on_progress or (lambda _msg: None)
        self.materials_root = MATERIALS_DIR
        os.makedirs(self.materials_root, exist_ok=True)

    def is_configured(self) -> bool:
        api_id, api_hash = _telegram_credentials()
        return bool(api_id and api_hash)

    def session_exists(self) -> bool:
        return os.path.exists(f"{SESSION_PATH}.session")

    def status_message(self) -> str:
        if not self.is_configured():
            return (
                "Telegram API_ID va API_HASH sozlanmagan. "
                "my.telegram.org dan oling va Sozlamalar → API ga kiriting."
            )
        if not self.session_exists():
            return (
                "Telegram sessiyasi yo'q. Terminalda bir marta: "
                "python -m src.telegram_auth"
            )
        return "Telegram tayyor — kanallarni sinxronlash mumkin."

    def _log(self, msg: str):
        safe = msg.encode("ascii", errors="replace").decode("ascii")
        self.on_progress(safe)

    async def _get_client(self):
        import asyncio
        from telethon import TelegramClient

        api_id, api_hash = _telegram_credentials()
        if not api_id or not api_hash:
            raise RuntimeError(self.status_message())

        last_err = None
        for attempt in range(12):
            client = TelegramClient(SESSION_PATH, int(api_id), api_hash)
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    await client.disconnect()
                    raise RuntimeError(
                        "Telegram sessiyasi yo'q. Terminalda: "
                        "python -m src.telegram_auth"
                    )
                return client
            except sqlite3.OperationalError as exc:
                last_err = exc
                if "locked" not in str(exc).lower():
                    raise
                try:
                    await client.disconnect()
                except Exception:
                    pass
                wait = min(2 * (attempt + 1), 15)
                self._log(
                    f"  Telegram sessiyasi band, {wait}s kutilmoqda..."
                )
                await asyncio.sleep(wait)
            except Exception:
                try:
                    await client.disconnect()
                except Exception:
                    pass
                raise

        raise RuntimeError(
            "Telegram sessiyasi qulflangan. Boshqa sync jarayonini "
            "to'xtating va IFA Mentor dasturini yoping.\n"
            f"Xato: {last_err}"
        )

    def _safe_filename(self, name: str, msg_id: int) -> str:
        base = re.sub(r'[<>:"/\\|?*]', "_", name or f"file_{msg_id}")
        return base[:180] or f"file_{msg_id}"

    def _get_message_filename(self, message) -> str:
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
            return f"Part_{message.id}.mp3"
        if message.voice:
            return f"voice_{message.id}.ogg"
        return ""

    def _message_has_file(self, message) -> bool:
        return bool(message.document or message.audio or message.voice)

    def _format_message_date(self, message) -> str:
        dt = getattr(message, "date", None)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return ""

    def _channel_dir(self, channel_slug: str, folder: str) -> str:
        return os.path.join(self.materials_root, "channels", channel_slug, folder)

    async def _download_to_folder(
        self,
        client,
        message,
        dest_dir: str,
        filename: str,
    ) -> Optional[str]:
        os.makedirs(dest_dir, exist_ok=True)
        save_path = os.path.join(dest_dir, filename)

        if os.path.exists(save_path):
            return save_path

        for attempt in range(4):
            try:
                path = await client.download_media(message, file=save_path)
                return path or save_path
            except Exception as exc:
                err = str(exc).lower()
                if attempt < 3 and (
                    "timeout" in err or "internal issues" in err
                ):
                    import asyncio
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                self._log(f"  WARN Yuklash ({filename}): {exc}")
                return None
        return None

    async def _save_material(
        self,
        client,
        message,
        channel_name: str,
        default_skill: str,
        existing_ids: set,
        set_info: dict,
        dest_dir: str,
        material_role: str = "",
        resolve_confidence: float = 0.0,
        resolve_status: str = "pending",
    ) -> bool:
        filename = self._get_message_filename(message)
        caption = message.message or ""

        if message.id in existing_ids:
            part_order = extract_part_number(filename, caption)
            self.db.update_material_set_by_msg(
                channel_name,
                message.id,
                set_info["set_id"],
                set_info["set_title"],
                part_order,
                material_role=material_role,
                resolve_confidence=resolve_confidence,
                resolve_status=resolve_status,
            )
            return False

        if not filename or detect_file_type(filename) == "other":
            return False

        meta = classify_message(
            filename=filename,
            caption=caption,
            text=caption,
            default_skill=default_skill,
            has_file=True,
        )

        part_order = extract_part_number(filename, caption)
        safe_name = self._safe_filename(filename, message.id)

        file_path = await self._download_to_folder(
            client,
            message,
            dest_dir,
            safe_name,
        )
        if not file_path:
            return False

        inserted = self.db.add_material(
            title=safe_name,
            file_path=file_path,
            file_type=meta["file_type"],
            skill="mock" if default_skill == "mock" else meta["skill"],
            level=meta["level"],
            channel=channel_name,
            msg_id=message.id,
            content_text=caption,
            category="mock_exam" if default_skill == "mock" else "file",
            tags=meta["tags"],
            set_id=set_info["set_id"],
            set_title=set_info["set_title"],
            part_order=part_order,
            message_date=self._format_message_date(message),
            material_role=material_role,
            resolve_confidence=resolve_confidence,
            resolve_status=resolve_status,
        )
        if inserted:
            existing_ids.add(message.id)
        return inserted

    async def _process_mock_bundle(
        self,
        client,
        bundle: MockBundle,
        channel_name: str,
        existing_ids: set,
    ) -> int:
        channel_slug = safe_set_slug(channel_name)
        dest_dir = self._channel_dir(channel_slug, bundle.folder)
        set_info = {
            "set_id": bundle.set_id,
            "set_title": bundle.set_title,
        }

        exam_id = self.db.upsert_mock_exam({
            "set_id": bundle.set_id,
            "set_title": bundle.set_title,
            "channel_name": channel_name,
            "day_number": bundle.day_number,
            "confidence": bundle.confidence,
            "status": bundle.status,
            "listening_count": len(bundle.listening),
            "reading_count": len(bundle.reading),
            "answers_count": len(bundle.answers),
            "notes": "; ".join(bundle.reasons),
        })

        if bundle.status == "review":
            self.db.add_mock_review_item(
                exam_id,
                bundle.set_id,
                bundle.set_title,
                channel_name,
                "; ".join(bundle.reasons),
                bundle.confidence,
            )

        count = 0
        for item in bundle.all_items:
            message = item.raw.raw
            if not message:
                continue
            if await self._save_material(
                client,
                message,
                channel_name,
                "mock",
                existing_ids,
                set_info,
                dest_dir,
                material_role=item.role,
                resolve_confidence=bundle.confidence,
                resolve_status=bundle.status,
            ):
                count += 1

        if count or bundle.all_items:
            tag = "AUTO" if bundle.status == "auto_attached" else "REVIEW"
            self._log(
                f"  [{tag}] {bundle.set_title}: {bundle.summary} "
                f"({int(bundle.confidence * 100)}%)"
            )
        return count

    async def _process_cluster(
        self,
        client,
        cluster,
        channel_name: str,
        default_skill: str,
        existing_ids: set,
    ) -> int:
        file_messages = [m for m in cluster if self._message_has_file(m)]
        if not file_messages:
            return 0

        set_info = build_set_info(file_messages, channel_name, default_skill)
        dest_dir = self._channel_dir(
            set_info["channel_slug"],
            set_info["folder"],
        )
        downloaded = 0

        for message in file_messages:
            if await self._save_material(
                client,
                message,
                channel_name,
                default_skill,
                existing_ids,
                set_info,
                dest_dir,
            ):
                downloaded += 1

        if downloaded:
            self._log(f"  📦 {set_info['set_title']}: {downloaded} ta fayl")
        return downloaded

    async def sync_channel(
        self,
        channel_ref: str,
        channel_name: str,
        skill: str,
        limit: int = 100,
    ) -> dict:
        from src.sync_lock import SyncLockError, clear_stale_sync_lock, telegram_sync_lock

        if skill == "mock" and limit < 500:
            limit = MOCK_SYNC_LIMIT

        clear_stale_sync_lock()
        try:
            with telegram_sync_lock(wait_seconds=60):
                return await self._sync_channel_impl(
                    channel_ref, channel_name, skill, limit
                )
        except SyncLockError as exc:
            self._log(f"❌ {exc}")
            return {
                "downloaded": 0,
                "skipped": 0,
                "channel": channel_name,
                "error": str(exc),
            }

    async def _sync_channel_impl(
        self,
        channel_ref: str,
        channel_name: str,
        skill: str,
        limit: int,
    ) -> dict:
        client = await self._get_client()
        downloaded = 0
        skipped = 0

        self._log(f"\n📡 {channel_name} ({channel_ref}) — {limit} ta post")
        existing_ids = self.db.get_material_message_ids(channel_name)
        already = len(existing_ids)
        if already:
            self._log(f"  ↩️  Davom etish: {already} ta post allaqachon bazada")

        try:
            entity = await client.get_entity(channel_ref)
            messages = []
            async for message in client.iter_messages(entity, limit=limit):
                if not self._message_has_file(message):
                    continue
                messages.append(message)

            self._log(f"  📥 Kanaldan {len(messages)} ta fayl-post o'qildi")

            if skill == "mock":
                pipeline = MockPipeline()
                result = await pipeline.run(
                    client, entity, channel_name, limit=limit
                )
                bundles = result["bundles"]
                self._log(
                    f"  Pipeline: {result['classified_count']} fayl, "
                    f"{len(bundles)} mock, "
                    f"auto={result['auto']}, review={result['review']}"
                )

                for i, bundle in enumerate(bundles, 1):
                    try:
                        count = await self._process_mock_bundle(
                            client, bundle, channel_name, existing_ids
                        )
                        downloaded += count
                        if i % 10 == 0 or count:
                            self._log(
                                f"  ... {i}/{len(bundles)} imtihon "
                                f"(+{downloaded} yangi fayl)"
                            )
                    except Exception as exc:
                        self._log(f"  WARN {bundle.set_title}: {exc}")
            else:
                clusters = cluster_messages(messages)
                self._log(f"  🔗 {len(clusters)} ta to'plam topildi")
                for cluster in clusters:
                    try:
                        count = await self._process_cluster(
                            client, cluster, channel_name, skill, existing_ids
                        )
                        downloaded += count
                        if count == 0:
                            skipped += len(cluster)
                    except Exception as exc:
                        self._log(f"  ⚠️ To'plam xatosi: {exc}")
                        skipped += len(cluster)

        finally:
            try:
                await client.disconnect()
            except Exception as exc:
                self._log(f"  WARN Ulanish yopish: {exc}")

        self._log(f"✅ {channel_name}: +{downloaded} yangi, {skipped} o'tkazildi")
        return {"downloaded": downloaded, "skipped": skipped, "channel": channel_name}

    async def sync_all_channels(self, limit_per_channel: int = 100) -> dict:
        channels = self.db.get_active_channels()
        if not channels:
            self._log("⚠️ Hech qanday kanal qo'shilmagan")
            return {"total": 0, "channels": 0, "details": []}

        total = 0
        details = []
        self._log(f"\n🔄 {len(channels)} ta kanal sinxronlanmoqda...")

        for ch in channels:
            channel_ref = ch.get("channel_id") or ch.get("channel_name")
            ch_limit = limit_per_channel
            if ch.get("skill") == "mock":
                ch_limit = max(ch_limit, MOCK_SYNC_LIMIT)

            result = await self.sync_channel(
                channel_ref,
                ch["channel_name"],
                ch["skill"],
                limit=ch_limit,
            )
            count = result["downloaded"]
            total += count
            self.db.update_channel_sync(ch["id"], count)
            details.append(result)

        self._log(f"\n✅ Jami {total} ta yangi material qo'shildi")
        return {"total": total, "channels": len(channels), "details": details}

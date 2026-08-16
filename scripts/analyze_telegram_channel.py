"""Telegram kanal tuzilmasini tahlil qilish (fayl turlari, juftlash)."""

import argparse
import asyncio
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.telegram_channels import CHANNELS, get_channel_config
from src.telegram_pipeline import MockPipeline
from src.telegram_sync import TelegramSyncEngine


async def analyze(channel_ref: str, channel_name: str, limit: int = 200):
    engine = TelegramSyncEngine(Database())
    client = await engine._get_client()
    entity = await client.get_entity(channel_ref)

    pipeline = MockPipeline()
    result = await pipeline.run(client, entity, channel_name, limit=limit)
    bundles = result["bundles"]

    print(f"\n=== {channel_name} ({channel_ref}) ===")
    print(f"Xabarlar: {result['raw_count']}")
    print(f"Fayllar: {result['classified_count']}")
    print(f"To'plamlar: {len(bundles)}")
    print(f"Auto: {result['auto']}, Review: {result['review']}")

    role_counts = Counter()
    for bundle in bundles:
        for item in bundle.all_items:
            role_counts[item.role] += 1
    print("Rollar:", dict(role_counts))

    print("\nNamuna to'plamlar (10 ta):")
    for bundle in bundles[:10]:
        print(
            f"  {bundle.set_title} [{bundle.status}] "
            f"{int(bundle.confidence * 100)}% — {bundle.summary}"
        )

    risky = [
        b for b in bundles
        if b.listening and b.reading and b.confidence < 0.75
    ]
    if risky:
        print(f"\nShubhali juftlashlar: {len(risky)}")
        for bundle in risky[:5]:
            print(f"  - {bundle.set_title}: {', '.join(bundle.reasons)}")

    listening_only = [b for b in bundles if b.listening and not b.reading]
    print(f"\nFaqat listening: {len(listening_only)}")

    await client.disconnect()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("channel", nargs="?", default="mock")
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()

    ch = get_channel_config(args.channel)
    if not ch:
        for item in CHANNELS:
            if args.channel.lower() in item["label"].lower():
                ch = item
                break
    if not ch:
        print("Kanal topilmadi. Mavjud:")
        for item in CHANNELS:
            print(f"  - {item['channel_id']} ({item['label']})")
        sys.exit(1)

    asyncio.run(
        analyze(ch["channel_id"], ch["channel_name"], args.limit)
    )


if __name__ == "__main__":
    main()

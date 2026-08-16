"""Mock pipeline — to'liq oqim."""

from src.telegram_pipeline.file_classifier import FileClassifier
from src.telegram_pipeline.message_collector import MessageCollector
from src.telegram_pipeline.mock_resolver import MockBundle, MockResolver


class MockPipeline:
    """TELEGRAM → COLLECTOR → CLASSIFIER → RESOLVER"""

    def __init__(self):
        self.collector = MessageCollector()
        self.classifier = FileClassifier()
        self.resolver = MockResolver()

    async def run(self, client, entity, channel_name: str, limit: int = 2500):
        raw = await self.collector.collect_channel(
            client, entity, channel_name, limit=limit
        )
        classified = self.classifier.classify_batch(raw)
        bundles = self.resolver.resolve(classified, channel_name)
        return {
            "raw_count": len(raw),
            "classified_count": len(classified),
            "bundles": bundles,
            "auto": sum(1 for b in bundles if b.status == "auto_attached"),
            "review": sum(1 for b in bundles if b.status == "review"),
        }

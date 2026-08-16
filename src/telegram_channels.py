"""Asosiy Telegram kanallar — bitta manba."""

CHANNELS = [
    {
        "label": "Mock Exams (Multilevelzone)",
        "channel_name": "Multilevelzone Mock",
        "channel_id": "@Multilevelzone_mock",
        "skill": "mock",
        "pipeline": "mock",
        "sync_limit": 3500,
        "description": (
            "Kunlik mock: 1 PDF (savol+javob) + 6 ta listening audio"
        ),
    },
    {
        "label": "Halikulov (Tushganlar)",
        "channel_name": "Multilevel Halikulov",
        "channel_id": "https://t.me/Multilevel_tushganlar",
        "skill": "mock",
        "pipeline": "mock",
        "sync_limit": 2500,
        "description": (
            "Mock, listening, reading testlar — mock pipeline orqali juftlanadi"
        ),
    },
    {
        "label": "Grammar / Tenses",
        "channel_name": "Multilevel Zone Grammar",
        "channel_id": "https://t.me/Multilevelzone_grammar",
        "skill": "tenses",
        "pipeline": "cluster",
        "sync_limit": 500,
        "description": "Grammatika va zamonlar",
    },
    {
        "label": "Multilevel Zone",
        "channel_name": "Multilevel Zone",
        "channel_id": "https://t.me/Multilevel_zone",
        "skill": "mixed",
        "pipeline": "cluster",
        "sync_limit": 500,
        "description": "Aralash skill postlar",
    },
    {
        "label": "Multilevel Academy",
        "channel_name": "Multilevel Academy",
        "channel_id": "https://t.me/multilevel_academy",
        "skill": "mixed",
        "pipeline": "cluster",
        "sync_limit": 500,
        "description": "Aralash materiallar",
    },
]


def channel_slug(value: str) -> str:
    """Kanal kalitini solishtirish uchun normallashtirish."""
    v = (value or "").lower().strip()
    if "t.me/" in v:
        v = v.split("t.me/")[-1]
    return v.lstrip("@").replace(" ", "_")


def get_channel_config(channel_id_or_name: str) -> dict | None:
    needle = channel_slug(channel_id_or_name)
    if not needle:
        return None
    for ch in CHANNELS:
        keys = (
            ch["channel_id"],
            ch["channel_name"],
            ch["label"],
        )
        for key in keys:
            slug = channel_slug(key)
            if needle == slug or needle in slug or slug in needle:
                return ch
    return None

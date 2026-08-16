"""Mock kanal sync tugagach Halikulov rebuild ishga tushirish."""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "database", "telegram_sync.lock")


def mock_sync_running() -> bool:
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" "
                "| Where-Object { $_.CommandLine -like '*rebuild_channel.py mock*' "
                "-or $_.CommandLine -like '*sync_mock_channel.py*' } "
                "| Select-Object -ExpandProperty ProcessId",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        pids = [p.strip() for p in out.splitlines() if p.strip()]
        return len(pids) > 0
    except Exception:
        return os.path.exists(LOCK)


def mock_ready() -> bool:
    """Mock kanal yetarli yuklanganini tekshirish."""
    try:
        sys.path.insert(0, ROOT)
        from src.database import Database

        db = Database()
        materials = [
            m for m in db.get_all_materials()
            if m.get("source_channel") == "Multilevelzone Mock"
        ]
        pdfs = sum(1 for m in materials if m.get("file_type") == "pdf")
        audios = sum(1 for m in materials if m.get("file_type") == "audio")
        return pdfs >= 80 and audios >= 400
    except Exception:
        return False


def main():
    os.chdir(ROOT)
    print("Mock kanal sync tugashini kutyapman...", flush=True)
    while mock_sync_running():
        print(
            f"  ... hali ishlayapti ({time.strftime('%H:%M:%S')})",
            flush=True,
        )
        time.sleep(60)

    print("\nMock sync tugadi. Tayyorlik tekshirilmoqda...", flush=True)
    time.sleep(10)

    if not mock_ready():
        print(
            "Mock kanal hali to'liq emas. Halikulov o'tkazib yuborildi.",
            flush=True,
        )
        sys.exit(0)

    if os.path.exists(LOCK):
        try:
            os.remove(LOCK)
        except OSError:
            pass

    print("=== Halikulov rebuild boshlanmoqda ===\n", flush=True)
    result = subprocess.run(
        [sys.executable, "scripts/rebuild_channel.py", "halikulov"],
        cwd=ROOT,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

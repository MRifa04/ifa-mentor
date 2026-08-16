"""Bitta vaqtda faqat bitta Telegram sync ishlashi uchun qulf."""

import os
import sys
import time
from contextlib import contextmanager

from config.settings import DATABASE_DIR

LOCK_PATH = os.path.join(DATABASE_DIR, "telegram_sync.lock")


class SyncLockError(RuntimeError):
    pass


def _is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_lock():
    if not os.path.exists(LOCK_PATH):
        return None
    try:
        with open(LOCK_PATH, "r", encoding="utf-8") as f:
            line = f.read().strip()
        if not line:
            return None
        pid_s, started = line.split("|", 1)
        return int(pid_s), started
    except Exception:
        return None


def clear_stale_sync_lock(max_age_seconds: int = 7200) -> bool:
    """O'lik jarayon yoki eski qulf faylini olib tashlash."""
    info = _read_lock()
    if not info:
        return False
    pid, started = info
    stale = not _is_pid_alive(pid)
    if not stale and started:
        try:
            lock_time = time.strptime(started, "%Y-%m-%d %H:%M:%S")
            age = time.time() - time.mktime(lock_time)
            stale = age > max_age_seconds
        except Exception:
            pass
    if stale:
        try:
            os.remove(LOCK_PATH)
            return True
        except OSError:
            return False
    return False


@contextmanager
def telegram_sync_lock(wait_seconds: int = 0):
    """Telegram sinxronlash uchun fayl qulfi."""
    info = _read_lock()
    if info and info[0] == os.getpid():
        yield
        return

    deadline = time.time() + wait_seconds
    while True:
        info = _read_lock()
        if info:
            pid, started = info
            if pid != os.getpid() and _is_pid_alive(pid):
                if time.time() >= deadline:
                    raise SyncLockError(
                        "Boshqa Telegram sync ishlayapti "
                        f"(PID {pid}, {started}).\n"
                        "Avval boshqa terminaldagi syncni to'xtating "
                        "yoki IFA Mentor dasturini yoping."
                    )
                time.sleep(2)
                continue
            try:
                os.remove(LOCK_PATH)
            except OSError:
                pass

        try:
            fd = os.open(
                LOCK_PATH,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(
                    f"{os.getpid()}|{time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            break
        except FileExistsError:
            if time.time() >= deadline:
                raise SyncLockError(
                    "Telegram sync qulfi band. Boshqa jarayonni to'xtating."
                )
            time.sleep(2)

    try:
        yield
    finally:
        try:
            if os.path.exists(LOCK_PATH):
                info = _read_lock()
                if info and info[0] == os.getpid():
                    os.remove(LOCK_PATH)
        except OSError:
            pass

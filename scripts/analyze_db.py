import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "database" / "ifa_mentor.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== CHANNELS ===")
for r in c.execute("SELECT * FROM telegram_channels"):
    print(dict(r))

print("\n=== MATERIALS BY CHANNEL ===")
for r in c.execute(
    """
    SELECT source_channel, skill, file_type, COUNT(*) n
    FROM materials GROUP BY source_channel, skill, file_type
    ORDER BY source_channel, n DESC
    """
):
    print(dict(r))

print("\n=== MOCK EXAMS ===")
for r in c.execute(
    "SELECT status, COUNT(*) n FROM mock_exams GROUP BY status"
):
    print(dict(r))

print("\n=== RESOLVE STATUS (Mock channel) ===")
for r in c.execute(
    """
    SELECT resolve_status, COUNT(*) n
    FROM materials
    WHERE source_channel LIKE '%Mock%'
    GROUP BY resolve_status
    """
):
    print(dict(r))

print("\n=== HALIKULOV SETS ===")
for r in c.execute(
    """
    SELECT set_id, set_title, COUNT(*) n,
           SUM(CASE WHEN file_type='audio' THEN 1 ELSE 0 END) aud,
           SUM(CASE WHEN file_type='pdf' THEN 1 ELSE 0 END) pdf
    FROM materials
    WHERE source_channel LIKE '%Halikulov%'
    GROUP BY set_id
  """
):
    print(dict(r))

print("\n=== ORPHAN AUDIO (no set) ===")
print(
    c.execute(
        """
        SELECT COUNT(*) FROM materials
        WHERE file_type='audio' AND (set_id IS NULL OR set_id='')
        """
    ).fetchone()[0]
)

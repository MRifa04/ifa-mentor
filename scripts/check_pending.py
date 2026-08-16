import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "database" / "ifa_mentor.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

ch = "Multilevelzone Mock"
pending = c.execute(
    "SELECT COUNT(*) FROM materials WHERE source_channel=? AND resolve_status='pending'",
    (ch,),
).fetchone()[0]
with_set = c.execute(
    """
    SELECT COUNT(*) FROM materials
    WHERE source_channel=? AND resolve_status='pending'
      AND set_id IS NOT NULL AND set_id != ''
    """,
    (ch,),
).fetchone()[0]
print(f"pending={pending}, with_set_id={with_set}")
print("Top sets:")
for r in c.execute(
    "SELECT set_id, COUNT(*) n FROM materials WHERE source_channel=? GROUP BY set_id ORDER BY n DESC LIMIT 8",
    (ch,),
):
    print(dict(r))

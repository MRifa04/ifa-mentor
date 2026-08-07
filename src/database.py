import sqlite3
import json
import os
from datetime import datetime
from config.settings import BASE_DIR

DB_PATH = os.path.join(BASE_DIR, "database", "ifa_mentor.db")

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = None
        self.create_tables()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()

        # Foydalanuvchi jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY,
                name TEXT,
                current_level TEXT DEFAULT 'B1',
                target_level TEXT DEFAULT 'B2',
                target_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessiya natijalari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                skill TEXT,
                score INTEGER,
                max_score INTEGER,
                percentage REAL,
                duration_minutes INTEGER,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Har bir part natijalari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS part_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                skill TEXT,
                part_name TEXT,
                level TEXT,
                correct INTEGER,
                total INTEGER,
                percentage REAL,
                question_type TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # Study DNA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_dna (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill TEXT,
                question_type TEXT,
                total_attempts INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                percentage REAL DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Progress (kunlik)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                listening REAL DEFAULT 0,
                reading REAL DEFAULT 0,
                writing REAL DEFAULT 0,
                speaking REAL DEFAULT 0,
                vocabulary REAL DEFAULT 0,
                overall REAL DEFAULT 0
            )
        """)

        # Vocabulary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE,
                uzbek TEXT,
                pronunciation TEXT,
                definition TEXT,
                example_ai TEXT,
                example_book TEXT,
                source_material TEXT,
                level TEXT,
                status TEXT DEFAULT 'new',
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                next_review TEXT,
                last_reviewed TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Materiallar (Telegram dan kelgan)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                file_path TEXT,
                file_type TEXT,
                skill TEXT,
                level TEXT,
                source_channel TEXT,
                telegram_message_id INTEGER,
                is_used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kunlik plan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                skill TEXT,
                task_type TEXT,
                material_id INTEGER,
                duration_minutes INTEGER,
                is_completed INTEGER DEFAULT 0,
                score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Telegram kanallar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT,
                channel_id TEXT,
                skill TEXT,
                is_active INTEGER DEFAULT 1,
                last_sync TEXT,
                total_materials INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Boshlang'ich foydalanuvchi
        cursor.execute("""
            INSERT OR IGNORE INTO user (id, name, current_level, target_level, target_date)
            VALUES (1, 'Ilhom', 'B1', 'B2', '2026-10-01')
        """)

        # Boshlang'ich progress (sertifikat ballari)
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT OR IGNORE INTO progress (date, listening, reading, writing, speaking, overall)
            VALUES (?, 49, 55, 43, 35, 46)
        """, (today,))

        conn.commit()
        self.close()
        print("✅ Database yaratildi:", DB_PATH)

    # ─── SESSIONS ───────────────────────────────────────────

    def save_session(self, skill, score, max_score, duration, details=None):
        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        percentage = round((score / max_score) * 100, 1) if max_score > 0 else 0
        cursor.execute("""
            INSERT INTO sessions (date, skill, score, max_score, percentage, duration_minutes, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (today, skill, score, max_score, percentage, duration, json.dumps(details or {})))
        session_id = cursor.lastrowid
        conn.commit()
        self.close()
        return session_id

    def save_part_result(self, session_id, skill, part_name, level, correct, total, question_type):
        conn = self.connect()
        cursor = conn.cursor()
        percentage = round((correct / total) * 100, 1) if total > 0 else 0
        cursor.execute("""
            INSERT INTO part_results (session_id, skill, part_name, level, correct, total, percentage, question_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, skill, part_name, level, correct, total, percentage, question_type))
        conn.commit()
        self.close()

    # ─── STUDY DNA ──────────────────────────────────────────

    def update_study_dna(self, skill, question_type, correct, total):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM study_dna WHERE skill=? AND question_type=?
        """, (skill, question_type))
        row = cursor.fetchone()
        if row:
            new_attempts = row["total_attempts"] + total
            new_correct = row["correct_answers"] + correct
            new_pct = round((new_correct / new_attempts) * 100, 1)
            cursor.execute("""
                UPDATE study_dna
                SET total_attempts=?, correct_answers=?, percentage=?, last_updated=CURRENT_TIMESTAMP
                WHERE skill=? AND question_type=?
            """, (new_attempts, new_correct, new_pct, skill, question_type))
        else:
            pct = round((correct / total) * 100, 1) if total > 0 else 0
            cursor.execute("""
                INSERT INTO study_dna (skill, question_type, total_attempts, correct_answers, percentage)
                VALUES (?, ?, ?, ?, ?)
            """, (skill, question_type, total, correct, pct))
        conn.commit()
        self.close()

    def get_weak_points(self, threshold=60):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT skill, question_type, percentage
            FROM study_dna
            WHERE percentage < ?
            ORDER BY percentage ASC
        """, (threshold,))
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    # ─── PROGRESS ───────────────────────────────────────────

    def update_progress(self, skill, score):
        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT * FROM progress WHERE date=?", (today,))
        row = cursor.fetchone()
        if row:
            cursor.execute(f"""
                UPDATE progress SET {skill}=? WHERE date=?
            """, (score, today))
        else:
            cursor.execute(f"""
                INSERT INTO progress (date, {skill}) VALUES (?, ?)
            """, (today, score))
        conn.commit()
        self.close()

    def get_progress_history(self, days=30):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM progress
            ORDER BY date DESC
            LIMIT ?
        """, (days,))
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    # ─── VOCABULARY ─────────────────────────────────────────

    def add_word(self, word, uzbek="", pronunciation="", definition="",
                 example_ai="", example_book="", source="", level="B2"):
        conn = self.connect()
        cursor = conn.cursor()
        from datetime import timedelta
        next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO vocabulary
                (word, uzbek, pronunciation, definition, example_ai,
                 example_book, source_material, level, next_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (word, uzbek, pronunciation, definition,
                  example_ai, example_book, source, level, next_review))
            conn.commit()
        except Exception as e:
            print(f"So'z qo'shishda xato: {e}")
        self.close()

    def get_words_for_review(self):
        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM vocabulary
            WHERE next_review <= ? AND status != 'mastered'
            ORDER BY next_review ASC
            LIMIT 15
        """, (today,))
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    def update_word_review(self, word_id, correct):
        conn = self.connect()
        cursor = conn.cursor()
        from datetime import timedelta
        cursor.execute("SELECT * FROM vocabulary WHERE id=?", (word_id,))
        word = cursor.fetchone()
        if not word:
            self.close()
            return
        intervals = [1, 3, 7, 14, 30]
        correct_count = word["correct_count"] + (1 if correct else 0)
        wrong_count = word["wrong_count"] + (0 if correct else 1)
        idx = min(correct_count, len(intervals) - 1)
        next_review = (datetime.now() + timedelta(days=intervals[idx])).strftime("%Y-%m-%d")
        status = "mastered" if correct_count >= 5 else "learning"
        cursor.execute("""
            UPDATE vocabulary
            SET correct_count=?, wrong_count=?, next_review=?,
                status=?, last_reviewed=CURRENT_TIMESTAMP
            WHERE id=?
        """, (correct_count, wrong_count, next_review, status, word_id))
        conn.commit()
        self.close()

    # ─── MATERIALLAR ────────────────────────────────────────

    def add_material(self, title, file_path, file_type, skill, level, channel, msg_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO materials
            (title, file_path, file_type, skill, level, source_channel, telegram_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, file_path, file_type, skill, level, channel, msg_id))
        conn.commit()
        self.close()

    def get_unused_material(self, skill, file_type=None):
        conn = self.connect()
        cursor = conn.cursor()
        if file_type:
            cursor.execute("""
                SELECT * FROM materials
                WHERE skill=? AND file_type=? AND is_used=0
                ORDER BY RANDOM() LIMIT 1
            """, (skill, file_type))
        else:
            cursor.execute("""
                SELECT * FROM materials
                WHERE skill=? AND is_used=0
                ORDER BY RANDOM() LIMIT 1
            """, (skill,))
        row = cursor.fetchone()
        self.close()
        return dict(row) if row else None

    def mark_material_used(self, material_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE materials SET is_used=1 WHERE id=?", (material_id,))
        conn.commit()
        self.close()

    # ─── TELEGRAM KANALLAR ──────────────────────────────────

    def add_channel(self, channel_name, channel_id, skill):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO telegram_channels (channel_name, channel_id, skill)
            VALUES (?, ?, ?)
        """, (channel_name, channel_id, skill))
        conn.commit()
        self.close()

    def get_active_channels(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM telegram_channels WHERE is_active=1")
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    # ─── DAILY PLAN ─────────────────────────────────────────

    def create_daily_plan(self, plans):
        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("DELETE FROM daily_plan WHERE date=?", (today,))
        for plan in plans:
            cursor.execute("""
                INSERT INTO daily_plan (date, skill, task_type, material_id, duration_minutes)
                VALUES (?, ?, ?, ?, ?)
            """, (today, plan["skill"], plan["task_type"],
                  plan.get("material_id"), plan["duration"]))
        conn.commit()
        self.close()

    def get_today_plan(self):
        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM daily_plan WHERE date=? ORDER BY id ASC
        """, (today,))
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    def complete_plan_task(self, task_id, score):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE daily_plan SET is_completed=1, score=? WHERE id=?
        """, (score, task_id))
        conn.commit()
        self.close()


# Test
if __name__ == "__main__":
    db = Database()
    print("✅ Barcha jadvallar yaratildi!")
    print("📊 Weak points:", db.get_weak_points())
    print("📅 Today plan:", db.get_today_plan())
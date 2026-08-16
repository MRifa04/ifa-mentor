import sqlite3
import json
import os
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from config.settings import BASE_DIR, CURRENT_SCORES

DB_PATH = os.path.join(BASE_DIR, "database", "ifa_mentor.db")


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = None
        self._lock = threading.Lock()
        self._conn_open = False
        self._ensure_wal()
        self.create_tables()

    def _ensure_wal(self):
        """Bir nechta o'qish/yozish uchun WAL rejimini yoqish."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.commit()
        finally:
            conn.close()

    def connect(self):
        self._lock.acquire()
        self._conn_open = True
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                timeout=30,
                check_same_thread=False,
            )
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA busy_timeout=30000")
            return self.conn
        except Exception:
            self._conn_open = False
            self._lock.release()
            raise

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        finally:
            self.conn = None
            if self._conn_open:
                self._conn_open = False
                self._lock.release()

    @contextmanager
    def session(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.close()

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
                daily_minutes INTEGER DEFAULT 90,
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
                original_duration_minutes INTEGER,
                carryover_minutes INTEGER DEFAULT 0,
                carryover_source_date TEXT,
                carryover_processed INTEGER DEFAULT 0,
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tense_mastery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tense_key TEXT UNIQUE,
                mastery_pct REAL DEFAULT 0,
                breakdown_json TEXT,
                feedback TEXT,
                last_practiced TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tense_practice_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tense_key TEXT,
                level INTEGER,
                skill_area TEXT,
                correct INTEGER,
                total INTEGER,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Eski bazalar uchun daily_plan ustunlarini avtomatik qo'shish
        # (ALTER TABLE IF NOT EXISTS SQLite'da mavjud emas, shuning uchun tekshiramiz.)
        cursor.execute("PRAGMA table_info(daily_plan)")
        daily_columns = {row[1] for row in cursor.fetchall()}
        migrations = {
            "original_duration_minutes": "INTEGER",
            "carryover_minutes": "INTEGER DEFAULT 0",
            "carryover_source_date": "TEXT",
            "carryover_processed": "INTEGER DEFAULT 0",
        }
        for column, definition in migrations.items():
            if column not in daily_columns:
                cursor.execute(
                    f"ALTER TABLE daily_plan ADD COLUMN {column} {definition}"
                )

        cursor.execute("PRAGMA table_info(user)")
        user_columns = {row[1] for row in cursor.fetchall()}
        if "daily_minutes" not in user_columns:
            cursor.execute(
                "ALTER TABLE user ADD COLUMN daily_minutes INTEGER DEFAULT 90"
            )

        cursor.execute("PRAGMA table_info(materials)")
        material_columns = {row[1] for row in cursor.fetchall()}
        material_migrations = {
            "content_text": "TEXT",
            "category": "TEXT DEFAULT 'file'",
            "tags": "TEXT",
            "set_id": "TEXT",
            "set_title": "TEXT",
            "part_order": "INTEGER DEFAULT 0",
            "message_date": "TEXT",
            "material_role": "TEXT",
            "resolve_confidence": "REAL DEFAULT 0",
            "resolve_status": "TEXT DEFAULT 'pending'",
        }
        for column, definition in material_migrations.items():
            if column not in material_columns:
                cursor.execute(
                    f"ALTER TABLE materials ADD COLUMN {column} {definition}"
                )

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_material_channel_msg
            ON materials(source_channel, telegram_message_id)
            WHERE telegram_message_id IS NOT NULL AND telegram_message_id != 0
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id TEXT UNIQUE,
                set_title TEXT,
                channel_name TEXT,
                day_number INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0,
                status TEXT DEFAULT 'review',
                listening_count INTEGER DEFAULT 0,
                reading_count INTEGER DEFAULT 0,
                answers_count INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mock_exam_id INTEGER,
                set_id TEXT,
                set_title TEXT,
                channel_name TEXT,
                reason TEXT,
                confidence REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                FOREIGN KEY (mock_exam_id) REFERENCES mock_exams(id)
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
        print("Database yaratildi:", DB_PATH)

    # ─── USER ───────────────────────────────────────────────

    def get_user(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE id=1")
        row = cursor.fetchone()
        self.close()
        return dict(row) if row else None

    def update_user(
        self,
        name=None,
        current_level=None,
        target_level=None,
        target_date=None,
        daily_minutes=None,
    ):
        conn = self.connect()
        cursor = conn.cursor()
        fields = []
        values = []

        if name is not None:
            fields.append("name=?")
            values.append(name)
        if current_level is not None:
            fields.append("current_level=?")
            values.append(current_level)
        if target_level is not None:
            fields.append("target_level=?")
            values.append(target_level)
        if target_date is not None:
            fields.append("target_date=?")
            values.append(target_date)
        if daily_minutes is not None:
            fields.append("daily_minutes=?")
            values.append(int(daily_minutes))

        if not fields:
            self.close()
            return

        values.append(1)
        cursor.execute(
            f"UPDATE user SET {', '.join(fields)} WHERE id=?",
            values,
        )
        conn.commit()
        self.close()

    def clear_study_progress(self):
        """Sessiyalar va progress tarixini tozalaydi."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions")
        cursor.execute("DELETE FROM part_results")
        cursor.execute("DELETE FROM progress")
        cursor.execute("DELETE FROM study_dna")
        cursor.execute("DELETE FROM daily_plan")
        conn.commit()
        self.close()

    # ─── TENSES ENGINE ──────────────────────────────────────

    def ensure_tense_mastery(self):
        from src.tenses.registry import TENSE_ORDER
        conn = self.connect()
        cursor = conn.cursor()
        for key in TENSE_ORDER:
            cursor.execute("""
                INSERT OR IGNORE INTO tense_mastery
                (tense_key, mastery_pct, breakdown_json, feedback)
                VALUES (?, 0, '{}', '')
            """, (key,))
        conn.commit()
        self.close()

    def get_tense_mastery(self, tense_key):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tense_mastery WHERE tense_key=?",
            (tense_key,),
        )
        row = cursor.fetchone()
        self.close()
        if not row:
            return {"mastery_pct": 0, "breakdown": {}, "feedback": ""}
        data = dict(row)
        try:
            data["breakdown"] = json.loads(
                data.get("breakdown_json") or "{}"
            )
        except json.JSONDecodeError:
            data["breakdown"] = {}
        return data

    def get_all_tense_mastery(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tense_mastery ORDER BY mastery_pct ASC"
        )
        rows = cursor.fetchall()
        self.close()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["breakdown"] = json.loads(
                    item.get("breakdown_json") or "{}"
                )
            except json.JSONDecodeError:
                item["breakdown"] = {}
            result.append(item)
        return result

    def save_tense_mastery(
        self, tense_key, pct, breakdown, feedback=""
    ):
        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO tense_mastery
            (tense_key, mastery_pct, breakdown_json, feedback, last_practiced)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tense_key) DO UPDATE SET
                mastery_pct=excluded.mastery_pct,
                breakdown_json=excluded.breakdown_json,
                feedback=excluded.feedback,
                last_practiced=excluded.last_practiced,
                updated_at=CURRENT_TIMESTAMP
        """, (
            tense_key, pct, json.dumps(breakdown),
            feedback, today,
        ))
        conn.commit()
        self.close()

    def log_tense_practice(
        self, tense_key, level, skill_area,
        correct, total, details="",
    ):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tense_practice_log
            (tense_key, level, skill_area, correct, total, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tense_key, level, skill_area,
            correct, total, details,
        ))
        conn.commit()
        self.close()

    def get_tense_practice_summary(self, tense_key):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT skill_area,
                   SUM(correct) as correct,
                   SUM(total) as total
            FROM tense_practice_log
            WHERE tense_key=?
            GROUP BY skill_area
        """, (tense_key,))
        rows = cursor.fetchall()
        self.close()
        return {
            row["skill_area"]: {
                "correct": row["correct"] or 0,
                "total": row["total"] or 0,
            }
            for row in rows
        }

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

    def _baseline_progress_values(self):
        return {
            "listening": int(CURRENT_SCORES.get("listening", 0)),
            "reading": int(CURRENT_SCORES.get("reading", 0)),
            "writing": int(CURRENT_SCORES.get("writing", 0)),
            "speaking": int(CURRENT_SCORES.get("speaking", 0)),
            "vocabulary": int(CURRENT_SCORES.get("vocabulary", 0)),
            "overall": int(CURRENT_SCORES.get("overall", 0)),
        }

    def get_latest_progress(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM progress
            ORDER BY date DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        self.close()
        return dict(row) if row else None

    def update_progress(self, skill, score):
        allowed = {
            "listening",
            "reading",
            "writing",
            "speaking",
            "vocabulary",
        }
        if skill not in allowed:
            return

        conn = self.connect()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT * FROM progress WHERE date=?",
            (today,),
        )
        row = cursor.fetchone()

        if row:
            values = dict(row)
            values[skill] = score
        else:
            values = self._baseline_progress_values()
            cursor.execute("""
                SELECT * FROM progress
                ORDER BY date DESC
                LIMIT 1
            """)
            latest = cursor.fetchone()
            if latest:
                latest = dict(latest)
                for key in allowed.union({"overall"}):
                    if latest.get(key):
                        values[key] = latest[key]
            values[skill] = score

        main_skills = [
            values.get("listening", 0),
            values.get("reading", 0),
            values.get("writing", 0),
            values.get("speaking", 0),
        ]
        values["overall"] = round(
            sum(main_skills) / len(main_skills),
            1,
        )

        if row:
            cursor.execute("""
                UPDATE progress
                SET listening=?, reading=?, writing=?,
                    speaking=?, vocabulary=?, overall=?
                WHERE date=?
            """, (
                values["listening"],
                values["reading"],
                values["writing"],
                values["speaking"],
                values["vocabulary"],
                values["overall"],
                today,
            ))
        else:
            cursor.execute("""
                INSERT INTO progress
                (date, listening, reading, writing,
                 speaking, vocabulary, overall)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                today,
                values["listening"],
                values["reading"],
                values["writing"],
                values["speaking"],
                values["vocabulary"],
                values["overall"],
            ))

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

    def add_material(
        self,
        title,
        file_path,
        file_type,
        skill,
        level,
        channel,
        msg_id,
        content_text="",
        category="file",
        tags="",
        set_id="",
        set_title="",
        part_order=0,
        message_date="",
        material_role="",
        resolve_confidence=0.0,
        resolve_status="pending",
    ):
        params = (
            title, file_path, file_type, skill, level, channel, msg_id,
            content_text, category, tags, set_id, set_title, part_order,
            message_date, material_role, resolve_confidence, resolve_status,
        )
        for attempt in range(6):
            try:
                with self.session() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR IGNORE INTO materials
                        (title, file_path, file_type, skill, level,
                         source_channel, telegram_message_id,
                         content_text, category, tags,
                         set_id, set_title, part_order, message_date,
                         material_role, resolve_confidence, resolve_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, params)
                    return cursor.rowcount > 0
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower() and attempt < 5:
                    time.sleep(0.15 * (attempt + 1))
                    continue
                raise
        return False

    def update_material_set_by_msg(
        self, channel, msg_id, set_id, set_title, part_order=0,
        material_role="", resolve_confidence=0.0, resolve_status="pending",
    ):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE materials
                SET set_id=?, set_title=?, part_order=?,
                    material_role=?, resolve_confidence=?, resolve_status=?
                WHERE source_channel=? AND telegram_message_id=?
            """, (
                set_id, set_title, part_order,
                material_role, resolve_confidence, resolve_status,
                channel, msg_id,
            ))

    def upsert_mock_exam(self, bundle_dict):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mock_exams
                (set_id, set_title, channel_name, day_number, confidence,
                 status, listening_count, reading_count, answers_count, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(set_id) DO UPDATE SET
                    set_title=excluded.set_title,
                    confidence=excluded.confidence,
                    status=excluded.status,
                    listening_count=excluded.listening_count,
                    reading_count=excluded.reading_count,
                    answers_count=excluded.answers_count,
                    notes=excluded.notes,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                bundle_dict["set_id"],
                bundle_dict["set_title"],
                bundle_dict["channel_name"],
                bundle_dict.get("day_number", 0),
                bundle_dict.get("confidence", 0),
                bundle_dict.get("status", "review"),
                bundle_dict.get("listening_count", 0),
                bundle_dict.get("reading_count", 0),
                bundle_dict.get("answers_count", 0),
                bundle_dict.get("notes", ""),
            ))
            cursor.execute(
                "SELECT id FROM mock_exams WHERE set_id=?",
                (bundle_dict["set_id"],),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def delete_mock_exam(self, set_id: str):
        if not set_id:
            return
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM mock_review_queue WHERE set_id=?",
                (set_id,),
            )
            cursor.execute(
                "DELETE FROM mock_exams WHERE set_id=?",
                (set_id,),
            )

    def add_mock_review_item(
        self,
        mock_exam_id,
        set_id,
        set_title,
        channel_name,
        reason,
        confidence,
        payload="",
    ):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO mock_review_queue
                (mock_exam_id, set_id, set_title, channel_name,
                 reason, confidence, status, payload)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (
                mock_exam_id, set_id, set_title, channel_name,
                reason, confidence, payload,
            ))

    def get_mock_review_queue(self, status="pending"):
        with self.session() as conn:
            cursor = conn.cursor()
            if status == "all":
                cursor.execute("""
                    SELECT * FROM mock_review_queue
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT * FROM mock_review_queue
                    WHERE status=?
                    ORDER BY confidence ASC, created_at DESC
                """, (status,))
            return [dict(r) for r in cursor.fetchall()]

    def resolve_review_item(self, review_id, new_status="approved"):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mock_review_queue
                SET status=?, resolved_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (new_status, review_id))
            cursor.execute(
                "SELECT set_id FROM mock_review_queue WHERE id=?",
                (review_id,),
            )
            row = cursor.fetchone()
            if row and row[0]:
                cursor.execute("""
                    UPDATE mock_exams SET status='confirmed'
                    WHERE set_id=?
                """, (row[0],))
                cursor.execute("""
                    UPDATE materials SET resolve_status='confirmed'
                    WHERE set_id=?
                """, (row[0],))

    def clear_channel_materials(self, channel_name: str) -> int:
        """Kanal materiallarini bazadan o'chirish (fayllar qoladi)."""
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM materials WHERE source_channel=?",
                (channel_name,),
            )
            count = cursor.fetchone()[0]
            cursor.execute(
                "DELETE FROM materials WHERE source_channel=?",
                (channel_name,),
            )
            cursor.execute(
                "DELETE FROM mock_exams WHERE channel_name=?",
                (channel_name,),
            )
            cursor.execute(
                """
                DELETE FROM mock_review_queue
                WHERE channel_name=?
                """,
                (channel_name,),
            )
            return count

    def get_mock_exams(self, channel_name=None):
        with self.session() as conn:
            cursor = conn.cursor()
            if channel_name:
                cursor.execute("""
                    SELECT * FROM mock_exams
                    WHERE channel_name=?
                    ORDER BY day_number DESC
                """, (channel_name,))
            else:
                cursor.execute("""
                    SELECT * FROM mock_exams ORDER BY day_number DESC
                """)
            return [dict(r) for r in cursor.fetchall()]

    def update_material_set(
        self,
        material_id,
        set_id,
        set_title,
        part_order=0,
    ):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE materials
                SET set_id=?, set_title=?, part_order=?
                WHERE id=?
            """, (set_id, set_title, part_order, material_id))

    def organize_existing_materials(self):
        """Mock PDF + audio juftlash."""
        from src.telegram_grouping import (
            extract_day_number,
            extract_part_number,
            make_mock_set_id,
            parse_db_datetime,
        )

        with self.session() as conn:
            conn.execute("""
                UPDATE materials
                SET set_id='', set_title='', part_order=0
                WHERE set_id LIKE '%parts_pool%'
                   OR set_title='Listening Parts'
                   OR set_title LIKE 'Mock Test %'
            """)

        materials = self.get_all_materials()
        updated = 0

        mock_materials = [
            m for m in materials
            if m.get("skill") == "mock"
            or "mock" in (m.get("source_channel") or "").lower()
        ]
        if not mock_materials:
            mock_materials = [
                m for m in materials
                if m.get("file_type") in ("pdf", "audio")
            ]

        pdfs = []
        audios = []
        for mat in mock_materials:
            ft = mat.get("file_type")
            title = mat.get("title", "") or ""
            path = mat.get("file_path", "") or ""
            channel = mat.get("source_channel", "manual")
            blob = f"{title} {path}"

            if ft == "pdf":
                day = extract_day_number(blob)
                if day:
                    set_id = make_mock_set_id(channel, day)
                    set_title = f"Mock Day {day}"
                    self.update_material_set(mat["id"], set_id, set_title, 0)
                    pdfs.append({**mat, "day": day})
                    updated += 1
            elif ft == "audio":
                part = extract_part_number(title, path)
                if part:
                    audios.append({**mat, "part": part})

        by_channel = defaultdict(list)
        for a in audios:
            by_channel[a["source_channel"]].append(a)

        for channel, alist in by_channel.items():
            alist.sort(
                key=lambda x: x.get("message_date") or x.get("created_at") or ""
            )

            groups = []
            current = []
            for item in alist:
                if not current:
                    current = [item]
                    continue
                t0 = parse_db_datetime(
                    current[0].get("message_date") or current[0].get("created_at")
                )
                t1 = parse_db_datetime(
                    item.get("message_date") or item.get("created_at")
                )
                if t0 and t1 and abs((t1 - t0).total_seconds()) <= 180 and len(current) < 8:
                    current.append(item)
                else:
                    if len(current) >= 2:
                        groups.append(current)
                    current = [item]
            if len(current) >= 2:
                groups.append(current)

            channel_pdfs = [p for p in pdfs if p["source_channel"] == channel]
            used_pdf_ids = set()

            for group in groups:
                gt = parse_db_datetime(
                    group[0].get("message_date") or group[0].get("created_at")
                )
                best_pdf = None
                best_gap = 99999
                for pdf in channel_pdfs:
                    if pdf["id"] in used_pdf_ids:
                        continue
                    pt = parse_db_datetime(
                        pdf.get("message_date") or pdf.get("created_at")
                    )
                    if gt and pt:
                        gap = abs((gt - pt).total_seconds())
                        if gap <= 300 and gap < best_gap:
                            best_gap = gap
                            best_pdf = pdf

                if not best_pdf:
                    continue

                used_pdf_ids.add(best_pdf["id"])
                set_id = make_mock_set_id(channel, best_pdf["day"])
                set_title = f"Mock Day {best_pdf['day']}"
                for item in group:
                    self.update_material_set(
                        item["id"], set_id, set_title, item["part"]
                    )
                    updated += 1

        return updated

    def material_exists(self, channel, msg_id):
        if not msg_id:
            return False
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM materials
                WHERE source_channel=? AND telegram_message_id=?
                LIMIT 1
            """, (channel, msg_id))
            return cursor.fetchone() is not None

    def get_materials_by_set_id(self, set_id):
        if not set_id:
            return []
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM materials
                WHERE set_id=?
                ORDER BY
                    CASE file_type WHEN 'pdf' THEN 0 ELSE 1 END,
                    part_order ASC,
                    title ASC
            """, (set_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_material_message_ids(self, channel):
        """Kanal uchun mavjud post ID larni bir marta yuklash."""
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_message_id FROM materials
                WHERE source_channel=? AND telegram_message_id IS NOT NULL
            """, (channel,))
            return {row[0] for row in cursor.fetchall()}

    def get_all_materials(self):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM materials
                ORDER BY created_at DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def get_materials(
        self,
        skill=None,
        file_type=None,
        category=None,
        limit=None,
    ):
        conn = self.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM materials WHERE 1=1"
        params = []
        if skill and skill != "all":
            query += " AND skill=?"
            params.append(skill)
        if file_type and file_type != "all":
            query += " AND file_type=?"
            params.append(file_type)
        if category and category != "all":
            query += " AND category=?"
            params.append(category)
        query += " ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        self.close()
        return rows

    def get_tense_materials(self, tense_keyword=None, limit=20):
        """Tenses bo'limi uchun grammatika postlari."""
        conn = self.connect()
        cursor = conn.cursor()
        if tense_keyword:
            cursor.execute("""
                SELECT * FROM materials
                WHERE skill IN ('tenses', 'grammar')
                  AND (content_text LIKE ? OR title LIKE ? OR tags LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (f"%{tense_keyword}%", f"%{tense_keyword}%",
                  f"%{tense_keyword}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM materials
                WHERE skill IN ('tenses', 'grammar')
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        self.close()
        return rows

    def update_channel_sync(self, channel_id, count):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE telegram_channels
                SET last_sync=?, total_materials=total_materials+?
                WHERE id=?
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                count,
                channel_id,
            ))

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

    def create_daily_plan(self, plans, plan_date=None, replace=True):
        """
        Berilgan sana uchun kunlik reja yaratadi.

        Backward-compatible: oldingi chaqiruvlar plan_date bermasa bugunni ishlatadi.
        """
        conn = self.connect()
        cursor = conn.cursor()
        plan_date = plan_date or datetime.now().strftime("%Y-%m-%d")

        if replace:
            cursor.execute("DELETE FROM daily_plan WHERE date=?", (plan_date,))

        for plan in plans:
            duration = int(plan.get("duration", plan.get("duration_minutes", 0)) or 0)
            carryover = int(plan.get("carryover_minutes", 0) or 0)
            original = int(
                plan.get("original_duration_minutes", duration - carryover)
                or 0
            )
            cursor.execute("""
                INSERT INTO daily_plan
                (date, skill, task_type, material_id, duration_minutes,
                 is_completed, score, original_duration_minutes,
                 carryover_minutes, carryover_source_date, carryover_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan_date,
                plan["skill"],
                plan["task_type"],
                plan.get("material_id"),
                duration,
                int(plan.get("is_completed", 0) or 0),
                plan.get("score"),
                original,
                carryover,
                plan.get("carryover_source_date"),
                int(plan.get("carryover_processed", 0) or 0),
            ))

        conn.commit()
        self.close()

    def get_today_plan(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_plan_for_date(today)

    def get_plan_for_date(self, plan_date):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_plan
            WHERE date=? ORDER BY id ASC
        """, (plan_date,))
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    def get_pending_plan_tasks(self, start_date, end_date):
        """
        Berilgan oraliqdagi bajarilmagan va hali carry-over qilinmagan
        vazifalarni qaytaradi.
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_plan
            WHERE date >= ? AND date < ?
              AND is_completed = 0
              AND COALESCE(carryover_processed, 0) = 0
            ORDER BY date ASC, id ASC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        self.close()
        return [dict(r) for r in rows]

    def mark_plan_tasks_carried(self, task_ids):
        """
        Carry-over qilingan eski vazifalarni qayta taqsimlangan deb belgilaydi.
        0 = pending, 1 = completed, 2 = carried-over.
        """
        if not task_ids:
            return
        conn = self.connect()
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in task_ids)
        cursor.execute(
            f"UPDATE daily_plan SET is_completed=2, carryover_processed=1"
            f" WHERE id IN ({placeholders})",
            list(task_ids)
        )
        conn.commit()
        self.close()

    def complete_plan_task(self, task_id, score):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE daily_plan
            SET is_completed=1, score=?
            WHERE id=? AND is_completed=0
        """, (score, task_id))
        conn.commit()
        self.close()


# Test
if __name__ == "__main__":
    db = Database()
    print("✅ Barcha jadvallar yaratildi!")
    print("📊 Weak points:", db.get_weak_points())
    print("📅 Today plan:", db.get_today_plan())
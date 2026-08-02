import sqlite3
from typing import Optional
from config import Config
from utils import get_logger

logger = get_logger(__name__)

class Storage:
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS announcements (
                        id TEXT PRIMARY KEY,
                        pdf_hash TEXT,
                        headline TEXT,
                        company TEXT,
                        date TEXT,
                        processed BOOLEAN DEFAULT FALSE,
                        catalyst_score INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def announcement_exists(self, announcement_id: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM announcements WHERE id = ?", (announcement_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking if announcement exists: {e}")
            return False

    def insert_announcement(self, announcement_id: str, pdf_hash: str, headline: str, company: str, date: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO announcements (id, pdf_hash, headline, company, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (announcement_id, pdf_hash, headline, company, date))
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting announcement: {e}")

    def update_announcement(self, announcement_id: str, processed: bool, catalyst_score: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE announcements 
                    SET processed = ?, catalyst_score = ?
                    WHERE id = ?
                """, (processed, catalyst_score, announcement_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating announcement: {e}")

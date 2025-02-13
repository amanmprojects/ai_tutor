import sqlite3
from typing import List, Dict, Optional
import json
from config import DB_PATH

class Database:
    def __init__(self):
        # Instead of keeping a persistent connection, we'll create connections as needed
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(DB_PATH)

    def _init_db(self):
        with self._get_connection() as conn:
            self.create_tables(conn)

    def create_tables(self, conn):
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_topic TEXT,
                progress TEXT
            )
        ''')
        
        # Topics table for topic normalization
        conn.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_name TEXT UNIQUE,
                variations TEXT
            )
        ''')

        # Save topics user has previously learned
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_topics (
                user_id INTEGER,
                topic TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')

        # Save quiz data for each user
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quiz_data (
                user_id INTEGER,
                quiz TEXT,
                topic_id INTEGER,
                FOREIGN KEY(topic_id) REFERENCES topics(topic_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Initialize some common topics
        self._initialize_topics(conn)

    def _initialize_topics(self, conn):
        common_topics = {
            "Python": ["python", "py", "pythen", "pyth"],
            "JavaScript": ["javascript", "js", "java script"],
            "Java": ["java", "jva"],
            "Machine Learning": ["ml", "machine learning", "machinelearning"],
        }
        
        for topic, variations in common_topics.items():
            self.add_topic(topic, variations, conn)

    def add_topic(self, normalized_name: str, variations: List[str], conn=None):
        should_close = conn is None
        try:
            conn = conn or self._get_connection()
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO topics (normalized_name, variations) VALUES (?, ?)",
                    (normalized_name, json.dumps(variations))
                )
        finally:
            if should_close and conn:
                conn.close()

    def normalize_topic(self, topic: str) -> str:
        topic = topic.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT normalized_name, variations FROM topics")
            for row in cursor:
                normalized_name, variations = row[0], json.loads(row[1])
                if topic == normalized_name.lower() or topic in [v.lower() for v in variations]:
                    return normalized_name
        return topic.capitalize()

    def set_user_topic(self, user_id: int, topic: str) -> str:
        normalized_topic = self.normalize_topic(topic)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, current_topic, progress) VALUES (?, ?, ?)",
                (user_id, normalized_topic, json.dumps({}))
            )
        return normalized_topic

    def get_user_topic(self, user_id: int) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT current_topic FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def update_progress(self, user_id: int, topic: str, score: float):
        current = self.get_progress(user_id)
        current[topic] = score
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, current_topic, progress) VALUES (?, ?, ?)",
                (user_id, self.get_user_topic(user_id), json.dumps(current))
            )

    def get_progress(self, user_id: int) -> Dict[str, float]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT progress FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            return json.loads(result[0]) if result and result[0] else {}

    # def add_user_topics(self, user_id: int, topic: str):
    #     with self._get_connection() as conn:
    #     conn.execute(
    #         "INSERT INTO user_topics (user_id, topic) VALUES (?, ?)",
    #         (user_id, topic)
    #     )
    
    # def get_user_topics(self, user_id: int) -> List[str]:
    #     with self._get_connection() as conn:
    #         cursor = conn.execute(
    #             "SELECT topic FROM user_topics WHERE user_id = ?",
    #             (user_id,)
    #         )
    #         return [row[0] for row in cursor]
import sqlite3
from typing import List, Dict, Optional
import json
from config import DB_PATH

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # Users table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    current_topic TEXT,
                    progress TEXT
                )
            ''')
            
            # Topics table for topic normalization
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    normalized_name TEXT UNIQUE,
                    variations TEXT
                )
            ''')
            
            # Initialize some common topics
            self._initialize_topics()

    def _initialize_topics(self):
        common_topics = {
            "Python": ["python", "py", "pythen", "pyth"],
            "JavaScript": ["javascript", "js", "java script"],
            "Java": ["java", "jva"],
            "Machine Learning": ["ml", "machine learning", "machinelearning"],
        }
        
        for topic, variations in common_topics.items():
            self.add_topic(topic, variations)

    def add_topic(self, normalized_name: str, variations: List[str]):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT OR IGNORE INTO topics (normalized_name, variations) VALUES (?, ?)",
                    (normalized_name, json.dumps(variations))
                )
        except sqlite3.IntegrityError:
            pass

    def normalize_topic(self, topic: str) -> str:
        topic = topic.lower().strip()
        cursor = self.conn.execute("SELECT normalized_name, variations FROM topics")
        for row in cursor:
            normalized_name, variations = row[0], json.loads(row[1])
            if topic == normalized_name.lower() or topic in [v.lower() for v in variations]:
                return normalized_name
        return topic.capitalize()

    def set_user_topic(self, user_id: int, topic: str) -> str:
        normalized_topic = self.normalize_topic(topic)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO users (user_id, current_topic) VALUES (?, ?)",
                (user_id, normalized_topic)
            )
        return normalized_topic

    def get_user_topic(self, user_id: int) -> Optional[str]:
        cursor = self.conn.execute(
            "SELECT current_topic FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def update_progress(self, user_id: int, topic: str, score: float):
        current = self.get_progress(user_id)
        current[topic] = score
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO users (user_id, progress) VALUES (?, ?)",
                (user_id, json.dumps(current))
            )

    def get_progress(self, user_id: int) -> Dict[str, float]:
        cursor = self.conn.execute(
            "SELECT progress FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        return json.loads(result[0]) if result and result[0] else {}
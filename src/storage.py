import sqlite3
from enum import Enum
from typing import List, Optional
from contextlib import contextmanager

class ChatMode(Enum):
    TEXT = 1
    VOICE = 2

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('user_data.db')
    try:
        yield conn
    finally:
        conn.close()

class UserStorage:
    def __init__(self):
        self.init_db()
        self.update_existing_users()

    def init_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    chat_mode INTEGER,
                    is_processing BOOLEAN DEFAULT 0,
                    username TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Проверяем, существует ли колонка is_processing
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'is_processing' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN is_processing BOOLEAN DEFAULT 0')
            
            conn.commit()

    def update_existing_users(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_processing = 0 WHERE is_processing IS NULL")
            conn.commit()

    def get_user(self, user_id: int) -> Optional[dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                return {"user_id": user[0], "chat_mode": ChatMode(user[1]), "username": user[3]}
            return None

    def create_user(self, user_id: int, username: str, chat_mode: ChatMode = ChatMode.TEXT):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (user_id, chat_mode, username) VALUES (?, ?, ?)",
                           (user_id, chat_mode.value, username))
            conn.commit()

    def set_chat_mode(self, user_id: int, username: str, mode: ChatMode):
        self.create_user(user_id, username, mode)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET chat_mode = ? WHERE user_id = ?",
                           (mode.value, user_id))
            conn.commit()

    def get_chat_mode(self, user_id: int, username: str) -> ChatMode:
        user = self.get_user(user_id)
        if user:
            return user["chat_mode"]
        self.create_user(user_id, username)
        return ChatMode.TEXT

    def add_message(self, user_id: int, username: str, chat_in: str, chat_out: str):
        self.create_user(user_id, username)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            message = f"User say: {chat_in}\nBot say: {chat_out}"
            cursor.execute("INSERT INTO chat_history (user_id, message) VALUES (?, ?)",
                           (user_id, message))
            conn.commit()

    def get_chat_history(self, user_id: int) -> List[str]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT message FROM chat_history WHERE user_id = ? ORDER BY id",
                           (user_id,))
            return [row[0] for row in cursor.fetchall()]

    def set_processing_state(self, user_id: int, is_processing: bool):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_processing = ? WHERE user_id = ?",
                           (int(is_processing), user_id))
            conn.commit()

    def get_processing_state(self, user_id: int) -> bool:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_processing FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def update_username(self, user_id: int, username: str):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET username = ? WHERE user_id = ?",
                           (username, user_id))
            conn.commit()

# Создаем глобальный экземпляр хранилища пользователей
user_storage = UserStorage()

# Пример использования:
# user_storage.set_chat_mode(1, ChatMode.VOICE)
# user_storage.add_message(1, "Привет, как дела?")
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

    def init_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    chat_mode INTEGER
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
            conn.commit()

    def get_user(self, user_id: int) -> Optional[dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                return {"user_id": user[0], "chat_mode": ChatMode(user[1])}
            return None

    def create_user(self, user_id: int, chat_mode: ChatMode = ChatMode.TEXT):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (user_id, chat_mode) VALUES (?, ?)",
                           (user_id, chat_mode.value))
            conn.commit()

    def set_chat_mode(self, user_id: int, mode: ChatMode):
        self.create_user(user_id, mode)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET chat_mode = ? WHERE user_id = ?",
                           (mode.value, user_id))
            conn.commit()

    def get_chat_mode(self, user_id: int) -> ChatMode:
        user = self.get_user(user_id)
        if user:
            return user["chat_mode"]
        self.create_user(user_id)
        return ChatMode.TEXT

    def add_message(self, user_id: int, chat_in: str, chat_out: str):
        self.create_user(user_id)
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

# Создаем глобальный экземпляр хранилища пользователей
user_storage = UserStorage()

# Пример использования:
# user_storage.set_chat_mode(1, ChatMode.VOICE)
# user_storage.add_message(1, "Привет, как дела?")
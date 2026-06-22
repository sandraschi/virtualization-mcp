"""memory.py - SQLite-backed chat memory
Provides persistent storage of chat messages per session with a limit of 40 entries.
"""

import sqlite3
from pathlib import Path


class ChatMemory:
    def __init__(self, db_path: str, limit: int = 40):
        self.db_path = Path(db_path)
        self.limit = limit
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_memory (
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def get_messages(self, session_id: str) -> list[dict[str, str]]:
        """Return messages for the given session in chronological order."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM chat_memory WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)
            ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

    def append(self, session_id: str, role: str, content: str) -> None:
        """Add a new message and trim older messages to respect the limit."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chat_memory (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content)
            )
            # Trim excess rows
            conn.execute(
                """
                DELETE FROM chat_memory
                WHERE rowid NOT IN (
                    SELECT rowid FROM chat_memory
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ) AND session_id = ?;
                """,
                (session_id, self.limit, session_id),
            )
            conn.commit()

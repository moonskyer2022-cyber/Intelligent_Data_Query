import time
from typing import Optional

import pymysql

from settings import DB_CONNECT_TIMEOUT, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_READ_TIMEOUT, DB_USER, DB_WRITE_TIMEOUT, MAX_SESSIONS, SESSION_BACKEND, SESSION_TTL_SECONDS

MAX_TURNS = 6


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, list[dict[str, str]]] = {}
        self._last_access: dict[str, float] = {}

    def _connect(self):
        return pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            connect_timeout=DB_CONNECT_TIMEOUT,
            read_timeout=DB_READ_TIMEOUT,
            write_timeout=DB_WRITE_TIMEOUT,
        )

    def _expire(self) -> None:
        cutoff = time.time() - SESSION_TTL_SECONDS
        expired = [session_id for session_id, touched in self._last_access.items() if touched < cutoff]
        for session_id in expired:
            self._sessions.pop(session_id, None)
            self._last_access.pop(session_id, None)
        if len(self._sessions) > MAX_SESSIONS:
            oldest = sorted(self._last_access, key=self._last_access.get)[: len(self._sessions) - MAX_SESSIONS]
            for session_id in oldest:
                self._sessions.pop(session_id, None)
                self._last_access.pop(session_id, None)

    def get_history(self, session_id: Optional[str]) -> list[dict[str, str]]:
        if SESSION_BACKEND == "mysql" and session_id:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT role, content FROM aiquery_session_messages WHERE session_id=%s ORDER BY id DESC LIMIT %s",
                        (session_id, MAX_TURNS * 2),
                    )
                    rows = list(reversed(cur.fetchall()))
            return [{"role": row[0], "content": row[1]} for row in rows]
        self._expire()
        if not session_id:
            return []
        self._last_access[session_id] = time.time()
        return list(self._sessions.get(session_id, []))

    def format_history(self, session_id: Optional[str]) -> str:
        return self.format_messages(self.get_history(session_id))

    @staticmethod
    def format_messages(history: list[dict[str, str]]) -> str:
        if not history:
            return "（无历史对话）"
        return "\n".join(f"{m['role']}: {m['content']}" for m in history)

    def add_turn(self, session_id: Optional[str], question: str, answer: str) -> None:
        if SESSION_BACKEND == "mysql" and session_id:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO aiquery_session_messages (session_id, role, content) VALUES (%s, %s, %s)",
                        [(session_id, "user", question), (session_id, "assistant", answer)],
                    )
                conn.commit()
            return
        self._expire()
        if not session_id:
            return
        turns = self._sessions.setdefault(session_id, [])
        self._last_access[session_id] = time.time()
        turns.append({"role": "user", "content": question})
        turns.append({"role": "assistant", "content": answer})
        if len(turns) > MAX_TURNS * 2:
            self._sessions[session_id] = turns[-MAX_TURNS * 2 :]


session_store = SessionStore()

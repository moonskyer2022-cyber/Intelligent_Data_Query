from typing import Optional

MAX_TURNS = 6


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, list[dict[str, str]]] = {}

    def get_history(self, session_id: Optional[str]) -> list[dict[str, str]]:
        if not session_id:
            return []
        return list(self._sessions.get(session_id, []))

    def format_history(self, session_id: Optional[str]) -> str:
        history = self.get_history(session_id)
        if not history:
            return "（无历史对话）"
        return "\n".join(f"{m['role']}: {m['content']}" for m in history)

    def add_turn(self, session_id: Optional[str], question: str, answer: str) -> None:
        if not session_id:
            return
        turns = self._sessions.setdefault(session_id, [])
        turns.append({"role": "user", "content": question})
        turns.append({"role": "assistant", "content": answer})
        if len(turns) > MAX_TURNS * 2:
            self._sessions[session_id] = turns[-MAX_TURNS * 2 :]


session_store = SessionStore()

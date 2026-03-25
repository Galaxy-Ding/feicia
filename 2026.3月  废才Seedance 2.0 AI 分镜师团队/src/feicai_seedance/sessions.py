from __future__ import annotations

import json
import uuid
from pathlib import Path

from .models import SessionRecord


class SessionStore:
    def __init__(self, project_root: Path, sessions_root: Path) -> None:
        self.project_root = project_root
        self.sessions_root = sessions_root
        self.state_file = project_root / ".agent-state.json"

    def load_state(self) -> dict:
        if not self.state_file.exists():
            return {}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def save_state(self, state: dict) -> None:
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset_for_episode(self, episode: str) -> None:
        self.save_state(
            {
                "episode": episode,
                "director": "",
                "art-designer": "",
                "storyboard-artist": "",
            }
        )

    def get_or_create(self, episode: str, role: str) -> SessionRecord:
        state = self.load_state()
        if state.get("episode") != episode:
            self.reset_for_episode(episode)
            state = self.load_state()

        session_id = state.get(role) or f"{role}-{uuid.uuid4().hex[:12]}"
        history_path = self.sessions_root / episode / f"{role}.json"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        if not history_path.exists():
            history_path.write_text("[]", encoding="utf-8")

        state[role] = session_id
        state["episode"] = episode
        self.save_state(state)
        return SessionRecord(session_id=session_id, role=role, episode=episode, history_path=history_path)

    def load_history(self, record: SessionRecord) -> list[dict[str, str]]:
        return json.loads(record.history_path.read_text(encoding="utf-8"))

    def append_history(self, record: SessionRecord, messages: list[dict[str, str]]) -> None:
        history = self.load_history(record)
        history.extend(messages)
        record.history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

"""Local, bounded SQLite snapshot storage. No packet payloads or model objects."""

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4


from netsense.config import SESSION_DB

DEFAULT_PATH = SESSION_DB
MAX_SESSIONS = 50
MAX_SNAPSHOT_BYTES = 5_000_000


class SessionStore:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, saved_at TEXT NOT NULL,
                packet_count INTEGER NOT NULL, retained_count INTEGER NOT NULL,
                snapshot TEXT NOT NULL)""")
        except sqlite3.Error:
            db.close()
            raise
        return db

    def list_sessions(self):
        with closing(self._connect()) as db:
            return [dict(row) for row in db.execute(
                "SELECT id, name, saved_at, packet_count, retained_count FROM sessions ORDER BY saved_at DESC")]

    def save(self, name, snapshot):
        name = name.strip()
        if not name or len(name) > 80:
            raise ValueError("Use a session name between 1 and 80 characters.")
        if not snapshot["packets"]:
            raise ValueError("Capture at least one packet before saving a session.")
        saved_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        frozen = dict(snapshot, source_state=snapshot["state"], state="stopped",
                      packet_rate=None, byte_rate=None, last_packet_age=None,
                      saved_at=saved_at, session_name=name)
        payload = json.dumps({"version": 1, "snapshot": frozen}, allow_nan=False)
        if len(payload.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            raise ValueError("This snapshot exceeds the 5 MB session limit.")
        session_id = uuid4().hex
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] >= MAX_SESSIONS:
                raise ValueError("The library holds 50 sessions. Delete a saved session to make room.")
            db.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
                       (session_id, name, saved_at, snapshot["packet_count"], len(snapshot["packets"]), payload))
        return session_id

    def load(self, session_id):
        with closing(self._connect()) as db:
            row = db.execute("SELECT snapshot FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise ValueError("This saved session no longer exists.")
        try:
            payload = json.loads(row["snapshot"])
            if payload["version"] != 1:
                raise ValueError("Unsupported saved-session version.")
            return payload["snapshot"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("This saved session could not be read.") from exc

    def delete(self, session_id):
        with closing(self._connect()) as db, db:
            db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

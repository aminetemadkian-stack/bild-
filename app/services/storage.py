import json, sqlite3
from pathlib import Path
from app.core.config import settings

def connect():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id))")
        db.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL CHECK(role IN ('user','assistant')), content TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_expiry ON chat_history(expires_at)")

def save_project(project):
    with connect() as db:
        db.execute("INSERT INTO projects(id,payload,created_at) VALUES(?,?,?)", (project.id, project.model_dump_json(), project.created_at.isoformat()))

def get_project(project_id):
    with connect() as db:
        row=db.execute("SELECT payload FROM projects WHERE id=?",(project_id,)).fetchone()
    return json.loads(row["payload"]) if row else None

def save_run(run):
    with connect() as db:
        db.execute("INSERT INTO runs(id,project_id,payload,created_at) VALUES(?,?,?,?)", (run.id,run.project_id,run.model_dump_json(),run.created_at.isoformat()))

def get_run(run_id):
    with connect() as db:
        row=db.execute("SELECT payload FROM runs WHERE id=?",(run_id,)).fetchone()
    return json.loads(row["payload"]) if row else None


def cleanup_chat_history(now=None):
    """Delete expired chat rows. `now` is injectable to make expiry tests deterministic."""
    from datetime import datetime, timezone
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    with connect() as db:
        cur = db.execute("DELETE FROM chat_history WHERE expires_at <= ?", (now,))
        return cur.rowcount

def save_chat_exchange(user_text: str, assistant_text: str, retention_days: int, now=None):
    from datetime import datetime, timedelta, timezone
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = now + timedelta(days=retention_days)
    with connect() as db:
        db.executemany("INSERT INTO chat_history(role,content,created_at,expires_at) VALUES(?,?,?,?)", [
            ("user", user_text[:20000], now.isoformat(), expires.isoformat()),
            ("assistant", assistant_text[:20000], now.isoformat(), expires.isoformat())
        ])
        # Bound storage even if settings change or the cleanup loop has been offline.
        db.execute("DELETE FROM chat_history WHERE id NOT IN (SELECT id FROM chat_history ORDER BY id DESC LIMIT 500)")

def list_chat_history(limit: int = 200, now=None):
    cleanup_chat_history(now=now)
    with connect() as db:
        rows=db.execute("SELECT id,role,content,created_at,expires_at FROM chat_history ORDER BY id DESC LIMIT ?", (max(1,min(limit,500)),)).fetchall()
    return [dict(row) for row in reversed(rows)]

def clear_chat_history():
    with connect() as db:
        cur=db.execute("DELETE FROM chat_history")
        return cur.rowcount

def delete_message(message_id: int) -> bool:
    with connect() as db:
        cur = db.execute("DELETE FROM chat_history WHERE id = ?", (message_id,))
        return cur.rowcount > 0

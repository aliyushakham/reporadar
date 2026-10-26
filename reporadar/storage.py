"""Atomic SQLite snapshots and parameterized queries."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(Path(__file__).with_name("schema.sql").read_text())

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, snapshot):
        with self.connect() as db:
            run = db.execute("INSERT INTO runs(root,name,file_count,payload) VALUES (?,?,?,?)",
                (snapshot["root"], snapshot["name"], snapshot["file_count"], json.dumps(snapshot, ensure_ascii=False))).lastrowid
            db.executemany("INSERT INTO symbols VALUES (?,?,?,?,?,?,?)", [
                (run, s["id"], s["path"], s["name"], s["kind"], s["line"], s["end_line"]) for s in snapshot["symbols"]])
            db.executemany("INSERT INTO edges VALUES (?,?,?,?,?)", [
                (run, e["source"], e["target"], e["line"], e["reason"]) for e in snapshot["edges"]])
            db.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?)", [
                (run, d["id"], d["path"], d["title"], d["line"], d["text"]) for d in snapshot["documents"]])
        return run

    def load(self, run_id=None):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone() if run_id is not None else db.execute("SELECT payload FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            raise ValueError("Snapshot not found; run scan first")
        return json.loads(row["payload"])

    def runs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT id,created_at,name,file_count FROM runs ORDER BY id DESC LIMIT 100")]

PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    root TEXT NOT NULL,
    name TEXT NOT NULL,
    file_count INTEGER NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS symbols (
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    symbol_id TEXT NOT NULL,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    PRIMARY KEY (run_id, symbol_id)
);
CREATE TABLE IF NOT EXISTS edges (
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    line INTEGER NOT NULL,
    reason TEXT NOT NULL,
    FOREIGN KEY (run_id, source) REFERENCES symbols(run_id, symbol_id),
    FOREIGN KEY (run_id, target) REFERENCES symbols(run_id, symbol_id)
);
CREATE TABLE IF NOT EXISTS documents (
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    line INTEGER NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (run_id, document_id)
);
CREATE INDEX IF NOT EXISTS edges_target ON edges(run_id, target);
CREATE INDEX IF NOT EXISTS runs_root ON runs(root, id);

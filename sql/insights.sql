-- Replace :run_id with the snapshot id (or bind it through your SQL client).
-- Most referenced symbols: candidates for careful change review.
SELECT s.symbol_id, s.path, s.line, COUNT(e.source) AS incoming_references
FROM symbols s
LEFT JOIN edges e ON e.run_id = s.run_id AND e.target = s.symbol_id
WHERE s.run_id = :run_id
GROUP BY s.symbol_id, s.path, s.line
ORDER BY incoming_references DESC;

-- Snapshot size over time.
SELECT r.id, r.created_at, r.name, r.file_count,
       (SELECT COUNT(*) FROM symbols s WHERE s.run_id = r.id) AS symbols,
       (SELECT COUNT(*) FROM documents d WHERE d.run_id = r.id) AS document_sections
FROM runs r ORDER BY r.id;

-- Transitive callers, cycle-safe because UNION deduplicates.
WITH RECURSIVE callers(symbol_id) AS (
    SELECT source FROM edges WHERE run_id = :run_id AND target = :symbol_id
    UNION
    SELECT e.source FROM edges e JOIN callers c ON e.target = c.symbol_id
    WHERE e.run_id = :run_id
)
SELECT s.symbol_id, s.path, s.line FROM callers c
JOIN symbols s ON s.symbol_id = c.symbol_id AND s.run_id = :run_id
WHERE s.symbol_id != :symbol_id;

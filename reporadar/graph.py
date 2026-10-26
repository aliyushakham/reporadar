"""Call-graph traversal with shortest evidence paths and snapshot comparison."""
from collections import defaultdict, deque
from .search import related_documents


def impact(snapshot, symbol_id, direction="callers", depth=5):
    symbols = {s["id"]: s for s in snapshot["symbols"]}
    if symbol_id not in symbols:
        raise ValueError("Unknown symbol")
    if direction not in {"callers", "callees"} or not 1 <= depth <= 20:
        raise ValueError("direction must be callers/callees and depth must be 1..20")
    adjacency = defaultdict(list)
    for edge in snapshot["edges"]:
        a, b = (edge["target"], edge["source"]) if direction == "callers" else (edge["source"], edge["target"])
        adjacency[a].append((b, edge))
    seen, queue, affected = {symbol_id}, deque([(symbol_id, [])]), []
    while queue:
        current, path = queue.popleft()
        if len(path) >= depth:
            continue
        for target, edge in adjacency[current]:
            if target in seen:
                continue
            seen.add(target)
            chain = path + [edge]
            affected.append(dict(symbol=symbols[target], distance=len(chain), evidence=chain))
            queue.append((target, chain))
    return dict(symbol=symbols[symbol_id], direction=direction, depth=depth,
                affected=affected, documents=related_documents(snapshot, symbol_id),
                caveat="Static references only. Dynamic dispatch, runtime data flow and completeness are not guaranteed.")


def compare(old, new):
    before = {s["id"]: s for s in old["symbols"]}
    after = {s["id"]: s for s in new["symbols"]}
    changes = []
    for key in sorted(before.keys() | after.keys()):
        if key not in before:
            status = "added"
        elif key not in after:
            status = "removed"
        elif before[key]["fingerprint"] != after[key]["fingerprint"]:
            status = "modified"
        else:
            continue
        context = old if status == "removed" else new
        changes.append(dict(id=key, status=status, before=before.get(key), after=after.get(key),
            impact=impact(context, key),
            previous_callers=impact(old, key)["affected"] if key in before else []))
    return dict(changes=changes, count=len(changes),
                caveat="Renames appear as removed + added. Documentation matches are review suggestions, not proven errors.")

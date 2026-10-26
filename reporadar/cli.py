"""Command-line entry points; JSON output can feed automation."""
import argparse
import json
import sys
from pathlib import Path
from .analyzer import analyze
from .storage import Store
from .search import SearchIndex
from .graph import impact, compare


def output(value, target=None):
    data = json.dumps(value, ensure_ascii=False, indent=2)
    if target:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(data + "\n", encoding="utf-8")
    else:
        print(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description="RepoRadar — evidence-first Python repository explorer")
    parser.add_argument("--db", default=".reporadar/index.sqlite", help="SQLite snapshot store")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Statically index a local repository")
    scan.add_argument("path")
    scan.add_argument("--output", help="Export full JSON snapshot")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--method", choices=["hybrid", "bm25", "identifier"], default="hybrid")
    search.add_argument("--run", type=int)
    trace = sub.add_parser("impact")
    trace.add_argument("symbol")
    trace.add_argument("--direction", choices=["callers", "callees"], default="callers")
    trace.add_argument("--depth", type=int, default=5)
    trace.add_argument("--run", type=int)
    diff = sub.add_parser("compare")
    diff.add_argument("before", type=int)
    diff.add_argument("after", type=int)
    sub.add_parser("runs")
    serve = sub.add_parser("serve")
    serve.add_argument("path", nargs="?", default="examples/shop")
    serve.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            from .server import make_server
            server = make_server(args.path, args.db, args.host, args.port)
            print(f"RepoRadar: http://127.0.0.1:{server.server_port} · {Path(args.path).resolve()}", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return
        store = Store(args.db)
        if args.command == "scan":
            snapshot = analyze(args.path)
            run = store.save(snapshot)
            if args.output:
                output(snapshot, args.output)
            output({"run_id": run, "files": snapshot["file_count"], "symbols": len(snapshot["symbols"]),
                    "edges": len(snapshot["edges"]), "documents": len(snapshot["documents"]), "warnings": snapshot["warnings"]})
        elif args.command == "search":
            output(SearchIndex(store.load(args.run)).search(args.query, method=args.method))
        elif args.command == "impact":
            output(impact(store.load(args.run), args.symbol, args.direction, args.depth))
        elif args.command == "compare":
            old, new = store.load(args.before), store.load(args.after)
            if old["root"] != new["root"]:
                raise ValueError("Snapshots must belong to the same repository")
            output(compare(old, new))
        else:
            output(store.runs())
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")

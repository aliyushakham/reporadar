"""Local HTTP app. One configured repository; no arbitrary file-path endpoints."""
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .analyzer import analyze
from .graph import impact, compare
from .search import SearchIndex
from .storage import Store

STATIC = Path(__file__).with_name("static")


def make_server(root, db_path, host="127.0.0.1", port=8765):
    root = Path(root).resolve()
    store = Store(db_path)
    run_id = store.save(analyze(root))
    lock = threading.Lock()
    state = {"run_id": run_id}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def reply(self, data, status=200, content_type="application/json; charset=utf-8"):
            body = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def trusted(self):
            authority = self.headers.get("Host", "")
            # Prevent DNS rebinding; docker service name is deliberately supported.
            hostname = authority.split(":")[0]
            if hostname not in {"127.0.0.1", "localhost", "reporadar"}:
                return False
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + authority:
                return False
            return True

        def do_GET(self):
            if not self.trusted():
                return self.reply({"error": "Host/origin not allowed"}, 403)
            route = urlparse(self.path)
            query = parse_qs(route.query)
            def arg(name, default=None):
                return query.get(name, [default])[0]
            try:
                if route.path == "/api/health":
                    return self.reply({"status": "ok", "version": "0.1.0"})
                if route.path == "/api/runs":
                    return self.reply(store.runs())
                run = int(arg("run", state["run_id"]))
                snapshot = store.load(run)
                if snapshot["root"] != str(root):
                    raise ValueError("Snapshot belongs to another repository")
                if route.path == "/api/snapshot":
                    public = {k: v for k, v in snapshot.items() if k != "root"}
                    return self.reply(dict(public, run_id=run))
                if route.path == "/api/search":
                    return self.reply(SearchIndex(snapshot).search(arg("q", "")[:1000],
                        limit=min(50, max(1, int(arg("limit", 12)))), method=arg("method", "hybrid")))
                if route.path == "/api/impact":
                    return self.reply(impact(snapshot, arg("symbol", ""), arg("direction", "callers"), int(arg("depth", 5))))
                if route.path == "/api/compare":
                    old = store.load(int(arg("before", 0)))
                    if old["root"] != snapshot["root"]:
                        raise ValueError("Snapshots must belong to the same repository")
                    return self.reply(compare(old, snapshot))
                files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
                if route.path in files:
                    file = STATIC / files[route.path]
                    return self.reply(file.read_bytes(), content_type=mimetypes.guess_type(file.name)[0] + "; charset=utf-8")
                return self.reply({"error": "Not found"}, 404)
            except (ValueError, TypeError) as exc:
                return self.reply({"error": str(exc)}, 400)

        def do_POST(self):
            if not self.trusted():
                return self.reply({"error": "Host/origin not allowed"}, 403)
            if self.path != "/api/scan":
                return self.reply({"error": "Not found"}, 404)
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.reply({"error": "application/json required"}, 415)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= 1024:
                    raise ValueError("Body too large")
                json.loads(self.rfile.read(length) or b"{}")
                if not lock.acquire(blocking=False):
                    return self.reply({"error": "A scan is already running"}, 409)
                try:
                    snapshot = analyze(root)
                    state["run_id"] = store.save(snapshot)
                finally:
                    lock.release()
                return self.reply({"run_id": state["run_id"], "symbols": len(snapshot["symbols"]),
                    "warnings": len(snapshot["warnings"])})
            except (ValueError, OSError) as exc:
                return self.reply({"error": str(exc)}, 400)

    return ThreadingHTTPServer((host, port), Handler)

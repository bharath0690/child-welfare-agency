"""Local dev server: static front end + /api on one port.

    python dev.py            # http://localhost:3000
    python dev.py --reseed   # rebuild data/cwa.db first

Reads a .env file in this folder if present (for DEEPSEEK_API_KEY). Never commit .env.
"""
import mimetypes
import os
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parent
env = ROOT / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

if "--reseed" in sys.argv:
    (ROOT / "data" / "cwa.db").unlink(missing_ok=True)

from cwa.api import app as api_app  # noqa: E402

BLOCKED = {".env", ".git", "data", "cwa", "tests", "api", "skills"}


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path.startswith("/api/"):
        return api_app(environ, start_response)
    rel = path.lstrip("/") or "index.html"
    if rel.split("/")[0] in BLOCKED:
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not found"]
    f = (ROOT / rel).resolve()
    if f.is_dir():
        f = f / "index.html"
    if not f.exists() and (ROOT / (rel + ".html")).exists():
        f = ROOT / (rel + ".html")
    if not str(f).startswith(str(ROOT)) or not f.is_file():
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not found"]
    start_response("200 OK", [("Content-Type", mimetypes.guess_type(str(f))[0] or "application/octet-stream"), ("Cache-Control", "no-store")])
    return [f.read_bytes()]


class Quiet(WSGIRequestHandler):
    def log_request(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    from cwa import db, llm
    db.connect()
    print(f"Agency AI prototype on http://localhost:{port}  (AI mode: {'live, ' + llm.model_name() if llm.enabled() else 'scripted'})")
    make_server("127.0.0.1", port, app, handler_class=Quiet).serve_forever()

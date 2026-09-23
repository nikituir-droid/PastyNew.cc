"""PastyNew.cc — Railway proxy (stdlib only, no deps).
Проксирует /validate /getscript /chunk на VPS, наружу торчит только
Railway-домен с HTTPS. База и бот остаются на VPS — сплит-брейна нет.
Env: PASTY_UPSTREAM=http://IP:8080 (обязательно), PORT (даёт Railway)."""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlreq
from urllib.error import HTTPError, URLError

UPSTREAM = os.environ.get("PASTY_UPSTREAM", "http://176.124.205.248:8080").rstrip("/")
PORT = int(os.environ.get("PORT", "8080"))
TIMEOUT = int(os.environ.get("PASTY_TIMEOUT", "60"))
ALLOWED = ("/", "/validate", "/getscript", "/chunk")


class Handler(BaseHTTPRequestHandler):
    server_version = "PastyProxy/1.0"

    def log_message(self, *a):
        pass  # тихо, чтобы не жечь лимиты логов

    def do_GET(self):
        path = (self.path or "/").split("?", 1)
        route, query = path[0], ("?" + path[1] if len(path) > 1 else "")
        if route not in ALLOWED:
            self._send(404, b"nope")
            return
        url = UPSTREAM + route + query
        try:
            req = urlreq.Request(url, method="GET",
                                 headers={"User-Agent": "PastyProxy/1.0"})
            with urlreq.urlopen(req, timeout=TIMEOUT) as r:
                self._send(r.status, r.read())
        except HTTPError as e:
            try:
                self._send(e.code, e.read())
            except Exception:
                self._send(502, b"upstream error")
        except (URLError, OSError, TimeoutError):
            self._send(502, b"upstream unreachable")

    def _send(self, code, body):
        data = body if isinstance(body, bytes) else str(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

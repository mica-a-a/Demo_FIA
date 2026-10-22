"""Mendoza Limpia · servidor HTTP (solo biblioteca estándar de Python). Uso: python server.py [puerto]"""
import json, os, re, sys, mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from app import db, models
from app.controllers import RUTAS
STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
class H(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        d = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)
    def _api(self, method):
        path = self.path.split("?")[0]
        for mt, rx, fn in RUTAS:
            mm = re.fullmatch(rx, path)
            if mt == method and mm:
                n = int(self.headers.get("Content-Length") or 0)
                try: body = json.loads(self.rfile.read(n) or b"{}")
                except ValueError: return self._json(400, {"error": "JSON inválido"})
                try: return self._json(*fn(body, mm.groups()))
                except models.Conflicto as e: return self._json(409, {"error": str(e)})
        self._json(404, {"error": "No encontrado"})
    def do_GET(self):
        if self.path.startswith("/api/"): return self._api("GET")
        f = "index.html" if self.path in ("/", "") else self.path.lstrip("/").split("?")[0]
        fp = os.path.normpath(os.path.join(STATIC, f))
        if not fp.startswith(STATIC) or not os.path.isfile(fp): return self._json(404, {"error": "No encontrado"})
        d = open(fp, "rb").read(); self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(fp)[0] or "text/plain") + "; charset=utf-8"); self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)
    def do_POST(self): self._api("POST")
    def log_message(self, *a): pass
if __name__ == "__main__":
    db.init(); port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"♻ Mendoza Limpia en http://localhost:{port}  (Ctrl+C para detener)"); ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()

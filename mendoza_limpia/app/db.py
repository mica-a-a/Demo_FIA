"""Persistencia en archivo JSON (data/datos.json), con bloqueo y escritura atómica.
Los datos iniciales (mock) están en data/datos_mock.json; «Reiniciar demo» los restaura."""
import os, json, shutil, threading, datetime, hashlib, secrets
from contextlib import contextmanager
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("ML_DATA", os.path.join(BASE, "data", "datos.json"))
MOCK = os.path.join(BASE, "data", "datos_mock.json")
_lock = threading.RLock()
USUARIOS = [("operador", "Operador de Higiene Urbana", "operador", "operador123"),
            ("admin", "Administración", "admin", "admin123"),
            ("dev", "Desarrollo", "desarrollador", "dev123")]   # credenciales de DEMO
def now(): return datetime.datetime.now().isoformat(timespec="seconds")
def hash_pw(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 60000).hex()
def load():
    with _lock, open(DATA, encoding="utf-8") as f: return json.load(f)
def save(d):
    with _lock:
        tmp = DATA + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA)
@contextmanager
def tx():
    """Lee, deja modificar y guarda todo junto (una operación a la vez)."""
    with _lock:
        d = load(); yield d; save(d)
def next_id(d, tabla):
    d["seq"][tabla] = d["seq"].get(tabla, 0) + 1; return d["seq"][tabla]
def _migrar():
    """Agrega usuarios, bloqueos y configuración si el archivo es de una versión anterior."""
    with tx() as d:
        d.setdefault("bloqueos", []); d.setdefault("config", {}); d["config"].setdefault("sal", secrets.token_hex(8))
        d["seq"].setdefault("bloqueos", 0); d["seq"].setdefault("usuarios", 0)
        if not d.get("usuarios"):
            d["usuarios"] = []
            for u, n, r, p in USUARIOS:
                s = secrets.token_hex(8); d["usuarios"].append({"id": next_id(d, "usuarios"), "usuario": u, "nombre": n, "rol": r, "salt": s, "hash": hash_pw(p, s)})
def init(reset=False):
    with _lock:
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        if reset or not os.path.exists(DATA): shutil.copyfile(MOCK, DATA)
        _migrar()
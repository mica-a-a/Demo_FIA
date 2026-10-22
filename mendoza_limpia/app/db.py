"""Persistencia en archivo JSON (data/datos.json), con bloqueo y escritura atómica.
Los datos iniciales (mock) están en data/datos_mock.json; «Reiniciar demo» los restaura."""
import os, json, shutil, threading, datetime
from contextlib import contextmanager
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("ML_DATA", os.path.join(BASE, "data", "datos.json"))
MOCK = os.path.join(BASE, "data", "datos_mock.json")
_lock = threading.RLock()
def now(): return datetime.datetime.now().isoformat(timespec="seconds")
def init(reset=False):
    with _lock:
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        if reset or not os.path.exists(DATA): shutil.copyfile(MOCK, DATA)
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

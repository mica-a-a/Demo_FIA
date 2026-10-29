"""Login por roles (operador, admin, desarrollador) con sesión en cookie HttpOnly."""
import secrets, time, threading, hmac
from http.cookies import SimpleCookie
from . import db
req = threading.local()          # datos de la petición en curso: user, ip, dev, ua, cookie
SES = {}
class Denegado(Exception):
    def __init__(self, code, msg): super().__init__(msg); self.code = code
def desde_cookie(header):
    c = SimpleCookie(header or ""); t = c.get("ml_sid"); s = SES.get(t.value) if t else None
    return s if s and s["exp"] > time.time() else None
def login(usuario, pw):
    d = db.load(); u = next((u for u in d["usuarios"] if u["usuario"] == (usuario or "").strip().lower()), None)
    if not u or not hmac.compare_digest(db.hash_pw(pw or "", u["salt"]), u["hash"]): raise Denegado(401, "Usuario o contraseña incorrectos")
    t = secrets.token_urlsafe(24); SES[t] = {"usuario": u["usuario"], "nombre": u["nombre"], "rol": u["rol"], "exp": time.time() + 8 * 3600}; return t, SES[t]
def logout():
    c = SimpleCookie(getattr(req, "cookie", "") or ""); t = c.get("ml_sid")
    if t: SES.pop(t.value, None)
def requerir(roles):
    u = getattr(req, "user", None)
    if not u: raise Denegado(401, "Tenés que iniciar sesión")
    if u["rol"] not in roles: raise Denegado(403, "No tenés permiso para esta acción")
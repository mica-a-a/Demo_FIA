"""Controladores: traducen cada petición HTTP a una operación del modelo. Cada ruta indica qué roles pueden usarla."""
from . import models as m, db, auth
OP, ADM, DEV = ("operador",), ("admin",), ("desarrollador",)
def _actor(): return "supervisor" if auth.req.user["rol"] == "admin" else "operador"   # el admin cumple el rol de Supervisor (N4)
def _ok():
    e = m.estado(); u = getattr(auth.req, "user", None)
    if not u: e = {"zonas": e["zonas"], "reportes": e["reportes"], "kpis": e["kpis"]}   # el público no ve datos internos
    e["yo"] = {"usuario": u["usuario"], "nombre": u["nombre"], "rol": u["rol"]} if u else None
    return 200, e
def get_estado(b, p): return _ok()
def post_login(b, p):
    t, s = auth.login(b.get("usuario"), b.get("password")); auth.req.user = s; c, e = _ok()
    return c, e, {"Set-Cookie": f"ml_sid={t}; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800"}
def post_logout(b, p):
    auth.logout(); auth.req.user = None; c, e = _ok(); return c, e, {"Set-Cookie": "ml_sid=; HttpOnly; Path=/; Max-Age=0"}
def post_contexto(b, p): m.set_contexto(b.get("clima", "normal"), b.get("turno", 0), b.get("evento", False)); return _ok()
def post_reporte(b, p):
    r = auth.req; m.crear_reporte(b.get("zona", ""), b.get("descripcion", ""), "vecino", b.get("tipo") or "Desborde de basura", b.get("direccion") or "", r.ip, r.dev, r.ua); return _ok()
def post_recolector(b, p): return 200, m.consultar_recolector(b.get("direccion", ""), b.get("zona") or None)
def post_validar(b, p): m.revisar_reporte(int(p[0]), True); return _ok()
def post_descartar(b, p): m.revisar_reporte(int(p[0]), False); return _ok()
def post_decidir(b, p): m.decidir(b.get("decision"), _actor(), b.get("zonas"), b.get("motivo")); return _ok()
def post_revisar(b, p): m.volver_a_revisar(); return _ok()
def post_escalar(b, p): m.escalar(); return _ok()
def post_despachar(b, p): m.despachar(_actor()); return _ok()
def post_salida(b, p): m.salida(); return _ok()
def post_resultado(b, p): m.resultado(b.get("contenedores", 0), b.get("desbordes", 0), b.get("verificaciones") or []); return _ok()
def post_nuevo(b, p): m.nuevo_turno(); return _ok()
def post_recal(b, p): m.decidir_recal(b.get("decision") == "aceptada"); return _ok()
def post_semana(b, p): m.nueva_semana(); return _ok()
def get_resumen(b, p): return 200, m.resumen()
def post_desbloquear(b, p): m.desbloquear(int(p[0])); return _ok()
def post_reset(b, p): db.init(reset=True); return _ok()
# (método, ruta, función, roles permitidos; None = público)
RUTAS = [("GET", r"/api/estado", get_estado, None), ("POST", r"/api/login", post_login, None), ("POST", r"/api/logout", post_logout, None),
 ("POST", r"/api/reportes", post_reporte, None), ("POST", r"/api/recolector", post_recolector, None),
 ("POST", r"/api/contexto", post_contexto, OP), ("POST", r"/api/reportes/(\d+)/validar", post_validar, OP), ("POST", r"/api/reportes/(\d+)/descartar", post_descartar, OP),
 ("POST", r"/api/propuesta/decidir", post_decidir, OP + ADM), ("POST", r"/api/propuesta/revisar", post_revisar, OP), ("POST", r"/api/propuesta/escalar", post_escalar, OP),
 ("POST", r"/api/despachar", post_despachar, OP + ADM), ("POST", r"/api/cuadrilla/salida", post_salida, OP), ("POST", r"/api/cuadrilla/resultado", post_resultado, OP),
 ("POST", r"/api/turno/nuevo", post_nuevo, OP), ("POST", r"/api/recalibracion/decidir", post_recal, ADM), ("POST", r"/api/recalibracion/semana", post_semana, ADM),
 ("GET", r"/api/admin/resumen", get_resumen, ADM + DEV), ("POST", r"/api/admin/desbloquear/(\d+)", post_desbloquear, ADM), ("POST", r"/api/demo/reset", post_reset, DEV)]
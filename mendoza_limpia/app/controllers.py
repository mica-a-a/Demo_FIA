"""Controladores: traducen cada petición HTTP a una operación del modelo y devuelven el estado."""
from . import models as m, db
def _ok(): return 200, m.estado()
def get_estado(b, p): return _ok()
def post_contexto(b, p): m.set_contexto(b.get("clima", "normal"), b.get("turno", 0), b.get("evento", False)); return _ok()
def post_reporte(b, p): m.crear_reporte(b.get("zona", ""), b.get("descripcion", ""), b.get("origen", "vecino"), b.get("tipo") or "Desborde de basura", b.get("direccion") or ""); return _ok()
def post_recolector(b, p): return 200, m.consultar_recolector(b.get("direccion", ""), b.get("zona") or None)
def post_validar(b, p): m.revisar_reporte(int(p[0]), True); return _ok()
def post_descartar(b, p): m.revisar_reporte(int(p[0]), False); return _ok()
def post_decidir(b, p): m.decidir(b.get("decision"), b.get("actor", "operador"), b.get("zonas"), b.get("motivo")); return _ok()
def post_revisar(b, p): m.volver_a_revisar(); return _ok()
def post_escalar(b, p): m.escalar(); return _ok()
def post_despachar(b, p): m.despachar(b.get("actor", "operador")); return _ok()
def post_salida(b, p): m.salida(); return _ok()
def post_resultado(b, p): m.resultado(b.get("contenedores", 0), b.get("desbordes", 0), b.get("verificaciones") or []); return _ok()
def post_nuevo(b, p): m.nuevo_turno(); return _ok()
def post_recal(b, p): m.decidir_recal(b.get("decision") == "aceptada"); return _ok()
def post_semana(b, p): m.nueva_semana(); return _ok()
def post_reset(b, p): db.init(reset=True); return _ok()
RUTAS = [("POST", r"/api/recolector", post_recolector),
("GET", r"/api/estado", get_estado),
("GET", r"/api/estado", get_estado), ("POST", r"/api/contexto", post_contexto), ("POST", r"/api/reportes", post_reporte),
 ("POST", r"/api/reportes/(\d+)/validar", post_validar), ("POST", r"/api/reportes/(\d+)/descartar", post_descartar),
 ("POST", r"/api/propuesta/decidir", post_decidir), ("POST", r"/api/propuesta/revisar", post_revisar), ("POST", r"/api/propuesta/escalar", post_escalar),
 ("POST", r"/api/despachar", post_despachar), ("POST", r"/api/cuadrilla/salida", post_salida), ("POST", r"/api/cuadrilla/resultado", post_resultado),
 ("POST", r"/api/turno/nuevo", post_nuevo), ("POST", r"/api/recalibracion/decidir", post_recal), ("POST", r"/api/recalibracion/semana", post_semana),
 ("POST", r"/api/demo/reset", post_reset)]

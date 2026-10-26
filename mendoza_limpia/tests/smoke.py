"""Prueba de humo del backend: recorre el flujo completo y verifica las reglas no delegables."""
import os, sys, tempfile
os.environ["ML_DATA"] = os.path.join(tempfile.mkdtemp(), "datos.json")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db, models as m
db.init()
def falla(f, *a):
    try: f(*a)
    except m.Conflicto: return True
    return False
e = m.estado(); assert e["propuesta"]["estado"] == "pendiente" and e["kpis"]["pendientes"] == 1
assert falla(m.despachar, "operador"), "N2: no se puede despachar sin decisión"
assert falla(m.decidir, "aprobada", "supervisor"), "N4: el Supervisor solo decide si hubo escalada"
m.crear_reporte("Bombal", "Basura en la vereda", "vecino"); assert m.estado()["kpis"]["total"] == 4
rid = m.estado()["reportes"][0]["id"]; m.revisar_reporte(rid, True)
assert falla(m.revisar_reporte, rid, True), "un reporte no se revisa dos veces"
m.decidir("aprobada", "operador"); m.set_contexto("lluvia", 1, False)
assert m.estado()["propuesta"]["estado"] == "pendiente", "cambiar el mapa invalida la decisión previa"
m.escalar(); m.decidir("aprobada", "supervisor"); m.despachar("supervisor")
assert falla(m.resultado, 3, 1), "primero se confirma la salida"
m.salida(); m.resultado(12, 2, [{"id": x["id"], "paso": True, "habia": True, "cuantos": 3} for x in m.estado()["verificar"]]); m.nuevo_turno()
assert m.estado()["propuesta"]["estado"] == "pendiente"
m.decidir("rechazada", "operador", motivo="Falta personal"); assert falla(m.despachar, "operador")
m.decidir_recal(True); assert falla(m.decidir_recal, True)
print("OK: todas las reglas del backend funcionan")

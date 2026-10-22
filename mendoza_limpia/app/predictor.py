"""Agente 1 (Predictor) y Agente 2 (Planificador): reglas simples y explicables, sin modelo entrenado."""
CLIMA = {"normal": 0.0, "lluvia": 0.15, "calor": 0.25}
def nivel(v): return "alto" if v >= .7 else "medio" if v >= .5 else "bajo"
def puntajes(ctx, zonas, validados):
    """puntaje = histórico del turno x (1 + clima) + 0.20 si hay evento en la zona + 0.15 por reporte validado."""
    out = []
    for z in zonas:
        base = z["hist_manana"] if ctx["turno"] == 0 else z["hist_tarde"]
        v = base * (1 + CLIMA[ctx["clima"]]) + (.2 if ctx["evento"] and z["afectada_evento"] else 0) + .15 * validados.get(z["id"], 0)
        v = min(1.0, v); out.append({"id": z["id"], "nombre": z["nombre"], "puntaje": round(v, 2), "nivel": nivel(v)})
    return sorted(out, key=lambda x: -x["puntaje"])
def ruta(pun): return [z["nombre"] for z in pun if z["nivel"] != "bajo"]

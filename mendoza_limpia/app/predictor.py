"""Agente 1 (Predictor) y Agente 2 (Planificador): reglas simples y explicables, sin modelo entrenado."""
CLIMA = {"normal": 0.0, "lluvia": 0.15, "calor": 0.25}
def nivel(v): return "alto" if v >= .7 else "medio" if v >= .5 else "bajo"
def puntajes(ctx, zonas, validados, saltos=None):
    """puntaje = histórico del turno x (1 + clima) + 0.20 si hay evento en la zona + 0.15 por reclamo validado
    + bonus por turnos sin visita (2 turnos: +0.10, 3: +0.20, 4 o más: +0.30), para que ninguna zona quede abandonada."""
    saltos = saltos or {}; out = []
    for z in zonas:
        base = z["hist_manana"] if ctx["turno"] == 0 else z["hist_tarde"]
        s = saltos.get(str(z["id"]), 0); bonus = min(.30, .10 * max(0, s - 1))
        v = base * (1 + CLIMA[ctx["clima"]]) + (.2 if ctx["evento"] and z["afectada_evento"] else 0) + .15 * validados.get(z["id"], 0) + bonus
        v = min(1.0, v); out.append({"id": z["id"], "nombre": z["nombre"], "puntaje": round(v, 2), "nivel": nivel(v), "saltos": s, "bonus": round(bonus, 2)})
    return sorted(out, key=lambda x: -x["puntaje"])
def ruta(pun): return [z["nombre"] for z in pun if z["nivel"] != "bajo"]          # prioritarias: riesgo medio y alto
def opcionales(pun): return [z["nombre"] for z in pun if z["nivel"] == "bajo"]    # se visitan si queda espacio y tiempo
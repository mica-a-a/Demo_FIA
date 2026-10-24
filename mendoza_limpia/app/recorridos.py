"""Horarios del recolector por zona (datos de prueba). Si el JSON trae la clave «recorridos», se usa esa."""
import unicodedata, datetime
DEF = {
 "Centro": {"horarios": [{"hora": "06:30", "turno": "Mañana"}, {"hora": "20:00", "turno": "Noche"}], "calles": ["San Martín", "Las Heras", "Sarmiento", "Mitre", "9 de Julio"]},
 "Quinta Sección": {"horarios": [{"hora": "07:00", "turno": "Mañana"}, {"hora": "19:30", "turno": "Noche"}], "calles": ["Emilio Civit", "Colón", "Montecaseros"]},
 "Sexta Sección": {"horarios": [{"hora": "08:00", "turno": "Mañana"}, {"hora": "21:00", "turno": "Noche"}], "calles": ["Boulogne Sur Mer", "Rioja", "Alem"]},
 "Bombal": {"horarios": [{"hora": "06:00", "turno": "Mañana"}, {"hora": "18:30", "turno": "Tarde"}], "calles": ["Bombal", "Patricias Mendocinas", "Olascoaga"]},
 "Parque": {"horarios": [{"hora": "09:00", "turno": "Mañana"}, {"hora": "22:00", "turno": "Noche"}], "calles": ["Libertador", "Grandes Capitanes", "Godoy Cruz"]},
 "Pedro Molina": {"horarios": [{"hora": "07:30", "turno": "Mañana"}, {"hora": "19:00", "turno": "Noche"}], "calles": ["Pedro Molina", "Juan B. Justo", "Ituzaingó"]}}
def _n(s): return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
def _fmt(mins): h, m = divmod(mins, 60); return f"{h} h {m} min" if h else f"{m} min"
def consultar(d, direccion, zona=None):
    from .models import Conflicto
    reg = d.get("recorridos") or DEF; q = _n(direccion); z = None; det = False
    for nom, info in reg.items():
        if any(_n(c) in q for c in info["calles"]): z, det = nom, True; break
    if not z and zona in reg: z = zona
    if not z: raise Conflicto("No reconocimos esa calle. Elegí tu zona en la lista o probá con: " + ", ".join(i["calles"][0] for i in reg.values()))
    a = datetime.datetime.now(); ahora = a.hour * 60 + a.minute; pasos = []
    for h in reg[z]["horarios"]:
        hh, mm = map(int, h["hora"].split(":")); t = hh * 60 + mm
        pasos.append({"hora": h["hora"], "turno": h["turno"], "paso": t <= ahora, "faltan": "" if t <= ahora else _fmt(t - ahora)})
    prox = next((p for p in pasos if not p["paso"]), None)
    msg = (f"Hoy pasa a las {prox['hora']} h (en {prox['faltan']})." if prox else
           f"Hoy el recolector ya pasó (último paso: {pasos[-1]['hora']} h). Mañana vuelve a las {pasos[0]['hora']} h.")
    ruta = any(p["estado"] == "despachada" and z in (p["ruta_final"] or []) for p in d["propuestas"])
    return {"zona": z, "detectada": det, "pasos": pasos, "mensaje": msg, "ruta_hoy": ruta}
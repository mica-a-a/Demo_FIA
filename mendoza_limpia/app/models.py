"""Modelos: reglas de negocio sobre el archivo JSON (incluye las decisiones no delegables N1–N4)."""
from collections import Counter
from . import predictor, recorridos, security
from . import db as _db
from .db import tx, now, next_id, load
class Conflicto(Exception): pass
def _log(d, msg, actor, texto): d["eventos_log"].append({"id": next_id(d, "eventos_log"), "mensaje": msg, "actor": actor, "texto": texto, "creado_en": now()})
def _mapa(d):
    val = Counter(r["zona_id"] for r in d["reportes"] if r["estado"] == "validado" and not r["usado"])
    return predictor.puntajes(d["contexto"], d["zonas"], val, d.get("saltos", {}))
def _ruta(d):
    pun = _mapa(d); return predictor.ruta(pun) + predictor.opcionales(pun), predictor.opcionales(pun)   # prioritarias primero, opcionales al final
def _actual(d):
    for p in reversed(d["propuestas"]):
        if p["estado"] != "cerrada": return p
    c = d["contexto"]
    p = {"id": next_id(d, "propuestas"), "turno": c["turno"], "clima": c["clima"], "evento": c["evento"], "ruta": _ruta(d)[0], "opcionales": _ruta(d)[1], "estado": "pendiente",
         "ruta_final": None, "motivo": None, "decidido_por": None, "escalada": 0, "creado_en": now(), "decidido_en": None}
    d["propuestas"].append(p); _log(d, "6", "Agente 2", "Propone ruta y frecuencia por turno (zonas de riesgo alto primero)"); return p
def _regenerar(d):
    """Si cambia el mapa de riesgo y la ruta aún no salió, la decisión previa queda obsoleta."""
    p = _actual(d)
    if p["estado"] != "despachada":
        c = d["contexto"]; p.update(turno=c["turno"], clima=c["clima"], evento=c["evento"], ruta=_ruta(d)[0], opcionales=_ruta(d)[1], estado="pendiente",
                                    ruta_final=None, motivo=None, decidido_por=None, decidido_en=None, escalada=0)
def _despacho(d):
    for p in reversed(d["propuestas"]):
        if p["estado"] == "despachada":
            for x in reversed(d["despachos"]):
                if x["propuesta_id"] == p["id"]: return x
    return None
def set_contexto(clima, turno, evento):
    if clima not in predictor.CLIMA: raise Conflicto("Clima inválido")
    with tx() as d:
        d["contexto"] = {"clima": clima, "turno": int(turno), "evento": int(bool(evento))}
        _log(d, "1", "Agente 1", f"Datos del día actualizados: clima {clima}, turno {'mañana' if int(turno)==0 else 'tarde'}"); _regenerar(d)
def crear_reporte(zona, desc, origen, tipo="Desborde de basura", direccion="", ip="0.0.0.0", dev="", ua=""):
    err = None
    with tx() as d:
        z = next((z for z in d["zonas"] if z["nombre"] == zona), None)
        if not z or not desc.strip() or origen not in ("vecino", "inspector"): raise Conflicto("Datos del reporte inválidos")
        h = security.huella(d, ip, dev, ua)
        try: security.controlar(d, h)
        except security.Bloqueado as e: err = str(e)      # el bloqueo queda guardado aunque se rechace el reclamo
        else:
            d["reportes"].append(dict({"id": next_id(d, "reportes"), "zona_id": z["id"], "descripcion": desc.strip()[:300], "origen": origen, "tipo": tipo.strip()[:60],
                                       "direccion": direccion.strip()[:120], "estado": "pendiente", "usado": 0, "creado_en": now(), "validado_en": None}, **h))
            _log(d, "0", origen.capitalize(), f"Informa «{tipo}» en {z['nombre']}")
    if err: raise Conflicto(err)
def revisar_reporte(rid, ok):
    with tx() as d:
        r = next((r for r in d["reportes"] if r["id"] == rid), None)
        if not r or r["estado"] != "pendiente": raise Conflicto("El reporte ya fue revisado")
        r["estado"] = "validado" if ok else "descartado"; r["validado_en"] = now()
        _log(d, "0", "Operador", ("Validó" if ok else "Descartó") + f" el reporte #{rid}")
        if ok: _regenerar(d)
def decidir(decision, actor, zonas=None, motivo=None):
    with tx() as d:
        p = _actual(d)
        if p["estado"] != "pendiente": raise Conflicto("La propuesta ya tiene una decisión")
        if actor not in ("operador", "supervisor"): raise Conflicto("Solo una persona autorizada puede decidir (N1)")
        if actor == "supervisor" and not p["escalada"]: raise Conflicto("El Supervisor decide solo si el Operador no respondió (N4)")
        ruta = list(p["ruta"])
        if decision == "ajustada":
            ruta = list(dict.fromkeys(z for z in (zonas or []) if z in ruta))  # respeta el orden elegido por la persona
            if not ruta: raise Conflicto("El ajuste no puede dejar la ruta vacía")
        elif decision == "rechazada": ruta = None
        elif decision != "aprobada": raise Conflicto("Decisión inválida")
        p.update(estado=decision, ruta_final=ruta, motivo=(motivo or "sin detalle") if decision == "rechazada" else None, decidido_por=actor, decidido_en=now())
        _log(d, "7", actor.capitalize(), {"aprobada": "Aprueba la ruta", "ajustada": "Ajusta y aprueba la ruta", "rechazada": "Rechaza: se mantiene la ruta habitual y se registra el motivo"}[decision])
def volver_a_revisar():
    with tx() as d:
        p = _actual(d)
        if p["estado"] == "rechazada": p.update(estado="pendiente", motivo=None, decidido_por=None, escalada=0)
def escalar():
    with tx() as d:
        p = _actual(d)
        if p["estado"] != "pendiente": raise Conflicto("No hay decisión pendiente para escalar")
        p["escalada"] = 1; _log(d, "2", "Agente 2", "Recordatorio al Operador: falta la aprobación"); _log(d, "3", "Agente 2", "Pide al Supervisor decidir: el Operador no responde")
def despachar(actor):
    with tx() as d:
        p = _actual(d)
        if p["estado"] not in ("aprobada", "ajustada"): raise Conflicto("No se puede despachar sin una ruta aprobada por una persona (N2)")
        d["despachos"].append({"id": next_id(d, "despachos"), "propuesta_id": p["id"], "ordenado_por": actor, "ordenado_en": now(),
                               "salida_confirmada_en": None, "contenedores": None, "desbordes": None, "resultado_en": None})
        p["estado"] = "despachada"; _log(d, "8", actor.capitalize(), "Ordena a la cuadrilla salir a recorrer la ruta aprobada")
def salida():
    with tx() as d:
        x = _despacho(d)
        if not x: raise Conflicto("Todavía no hay una ruta despachada")
        x["salida_confirmada_en"] = now(); _log(d, "9", "Cuadrilla", "Confirma la salida")
def _verificables(d):
    """Reclamos validados cuya zona estaba en la ruta despachada: la cuadrilla debe verificarlos."""
    x = _despacho(d)
    if not x or not x["salida_confirmada_en"] or x["resultado_en"]: return []
    p = next((p for p in reversed(d["propuestas"]) if p["estado"] == "despachada"), None)
    zn = {z["id"]: z["nombre"] for z in d["zonas"]}
    return [r for r in d["reportes"] if p and r["estado"] == "validado" and not r["usado"] and zn[r["zona_id"]] in (p["ruta_final"] or [])]
def _opcionales_verificar(d):
    """Zonas de riesgo bajo incluidas en la ruta despachada que la cuadrilla debe informar (si no tienen un reclamo que ya se verifica)."""
    x = _despacho(d); p = next((p for p in reversed(d["propuestas"]) if p["estado"] == "despachada"), None)
    if not x or not p or not x["salida_confirmada_en"] or x["resultado_en"]: return []
    zn = {z["id"]: z["nombre"] for z in d["zonas"]}; con_reclamo = {zn[r["zona_id"]] for r in _verificables(d)}
    return [z for z in (p["ruta_final"] or []) if z in p.get("opcionales", []) and z not in con_reclamo]
def resultado(cont, desb, verifs=None, opcionales=None):
    with tx() as d:
        x = _despacho(d)
        if not x or not x["salida_confirmada_en"]: raise Conflicto("Primero hay que confirmar la salida")
        ver = _verificables(d); ops = _opcionales_verificar(d); zn = {z["id"]: z["nombre"] for z in d["zonas"]}
        resp = {int(v.get("id", 0)): v for v in (verifs or [])}; respo = {v.get("zona"): v for v in (opcionales or [])}
        for r in ver:
            if r["id"] not in resp: raise Conflicto(f"Falta responder sobre el reclamo #{r['id']}")
        for z in ops:
            if z not in respo: raise Conflicto(f"Falta responder sobre la zona opcional {z}")
        lev = des = 0; visitadas = set()
        for r in ver:
            v = resp[r["id"]]
            if v.get("paso"):
                visitadas.add(zn[r["zona_id"]])
                if v.get("habia"):
                    n = max(0, int(v.get("cuantos") or 0)); r.update(estado="resuelto", levantados=n, comentario=None, resuelto_en=now()); lev += n; des += 1
                else: r.update(estado="no_constatado", comentario="Desborde inexistente: la cuadrilla pasó y no lo encontró", resuelto_en=now())
            else: r.update(estado="pendiente", comentario="No atendido: " + (v.get("motivo") or "sin motivo"), validado_en=None)
        for r in ver:
            if r["estado"] == "no_constatado": security.falta(d, r)
        regs = []
        for z in ops:                                   # zonas opcionales: ¿hubo espacio y tiempo? ¿se pasó? ¿había desborde?
            v = respo[z]; ok = bool(v.get("espacio")) and bool(v.get("paso"))
            reg = {"zona": z, "espacio": bool(v.get("espacio")), "paso": ok, "habia": None, "cuantos": None, "motivo": None}
            if ok:
                visitadas.add(z); reg["habia"] = bool(v.get("habia"))
                if reg["habia"]: n = max(0, int(v.get("cuantos") or 0)); reg["cuantos"] = n; lev += n; des += 1
            else: reg["motivo"] = v.get("motivo") or "sin motivo"
            regs.append(reg)
        p = next(p for p in reversed(d["propuestas"]) if p["estado"] == "despachada"); s = d.setdefault("saltos", {})
        visitadas |= {z for z in (p["ruta_final"] or []) if z not in p.get("opcionales", [])}   # las zonas prioritarias de la ruta se dan por recorridas
        for z in d["zonas"]:                            # turnos seguidos sin visita: sube la prioridad a partir del 2.º
            k = str(z["id"])
            if z["nombre"] in visitadas: s[k] = 0
            elif z["nombre"] in p.get("opcionales", []): s[k] = s.get(k, 0) + 1
        if ver or ops: cont, desb = lev, des
        x.update(contenedores=max(0, int(cont)), desbordes=max(0, int(desb)), resultado_en=now(), opcionales=regs)
        _log(d, "10", "Cuadrilla", f"Informa el resultado real de la calle ({len(ver)} reclamos y {len(ops)} zonas opcionales verificados)" if (ver or ops) else "Informa el resultado real de la calle al Operador")
def nuevo_turno():
    with tx() as d:
        p = _actual(d)
        if p["estado"] not in ("despachada", "rechazada"): raise Conflicto("El turno actual todavía no terminó")
        p["estado"] = "cerrada"
        _log(d, "-", "Sistema", "Nuevo turno: el Agente 2 prepara otra propuesta"); _actual(d)
def decidir_recal(ok):
    with tx() as d:
        r = d["recalibraciones"][-1]
        if r["estado"] != "propuesta": raise Conflicto("Ya hay una decisión para esta semana")
        r.update(estado="aceptada" if ok else "rechazada", decidido_por="supervisor", decidido_en=now())
        _log(d, "12", "Supervisor", "Acepta recalibrar el modelo" if ok else "Rechaza la recalibración")
def nueva_semana():
    with tx() as d:
        d["recalibraciones"].append({"id": next_id(d, "recalibraciones"), "precision": 72, "cobertura": 68, "km_var": -12, "estado": "propuesta", "decidido_por": None, "creado_en": now(), "decidido_en": None})
        _log(d, "11", "Agente 1", "Propone recalibrar: precisión por debajo del 75 %")
def estado():
    with tx() as d:
        zn = {z["id"]: z["nombre"] for z in d["zonas"]}; p = _actual(d)
        OCULTO = ("ip_hash", "dev_hash", "ip_mask", "ua")
        rep = [dict({k: v for k, v in r.items() if k not in OCULTO}, zona=zn[r["zona_id"]]) for r in reversed(d["reportes"])][:40]
        c = Counter(r["estado"] for r in d["reportes"])
        return {"contexto": d["contexto"], "zonas": _mapa(d), "propuesta": dict(p), "despacho": _despacho(d), "reportes": rep, "recal": d["recalibraciones"][-1],
                "opcionales_verificar": _opcionales_verificar(d),
                "verificar": [dict({k: v for k, v in r.items() if k not in OCULTO}, zona=zn[r["zona_id"]]) for r in _verificables(d)],
                "kpis": {"total": len(d["reportes"]), "pendientes": c["pendiente"], "validados": c["validado"], "descartados": c["descartado"], "resueltos": c["resuelto"]},
                "log": list(reversed(d["eventos_log"]))[:40]}
def consultar_recolector(direccion, zona=None): return recorridos.consultar(load(), direccion, zona)
def resumen():
    with tx() as d:
        ahora = now(); bl = [dict(b, vigente=bool(b["activo"] and b["hasta"] > ahora)) for b in reversed(d["bloqueos"])][:20]; g = {}
        for r in d["reportes"]:
            k = r.get("dev_hash")
            if not k: continue
            a = g.setdefault(k, {"dispositivo": k[:8], "ip": r.get("ip_mask"), "total": 0, "no_constatados": 0, "ultimo": ""})
            a["total"] += 1; a["no_constatados"] += r["estado"] == "no_constatado"; a["ultimo"] = max(a["ultimo"], r["creado_en"])
        return {"bloqueos": bl, "autores": sorted(g.values(), key=lambda a: -a["total"])[:10],
                "usuarios": [{"usuario": u["usuario"], "nombre": u["nombre"], "rol": u["rol"]} for u in d["usuarios"]],
                "datos": {"reportes": len(d["reportes"]), "archivo": _db.DATA}}
def desbloquear(bid):
    with tx() as d:
        b = next((b for b in d["bloqueos"] if b["id"] == bid), None)
        if not b: raise Conflicto("Bloqueo inexistente")
        b["activo"] = 0; _log(d, "-", "Admin", f"Desbloquea el dispositivo {b['dev_hash'][:6]}…")
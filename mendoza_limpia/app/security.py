"""Control de abuso: registro (hasheado) de IP y dispositivo, y bloqueo temporal por reclamos reiterados.
Regla: más de 3 reclamos en 10 min o más de 10 en 24 h → bloqueo 30 min; reincidencia → 1 h; luego 24 h.
Cada reclamo «no constatado» cuenta como falta (2 en 24 h bloquean)."""
import hashlib, datetime
from .db import now, next_id
DURACIONES = [30, 60, 1440]   # minutos: 1.º, 2.º, 3.º bloqueo en adelante
class Bloqueado(Exception): pass
def _h(sal, v): return hashlib.sha256((sal + v).encode()).hexdigest()[:16]
def _mask(ip):
    p = ip.split("."); return ".".join(p[:2] + ["x", "x"]) if len(p) == 4 else ip[:9] + "…"
def huella(d, ip, dev, ua):
    sal = d["config"]["sal"]
    return {"ip_hash": _h(sal, ip or "?"), "dev_hash": _h(sal, dev or "sin-dispositivo"), "ip_mask": _mask(ip or "?"), "ua": (ua or "")[:120]}
def _local(h): return (h.get("ip_mask") or "").startswith(("127.", "::1"))
def _mismo(x, h):
    """Mismo autor: mismo dispositivo, o misma IP (salvo localhost, que comparten todos en una demo local)."""
    return x.get("dev_hash") == h["dev_hash"] or (x.get("ip_hash") == h["ip_hash"] and not _local(h))
def _hace(minutos): return (datetime.datetime.now() - datetime.timedelta(minutes=minutos)).isoformat(timespec="seconds")
def activo(d, h):
    return next((b for b in d["bloqueos"] if b["activo"] and b["hasta"] > now() and _mismo(b, h)), None)
def _bloquear(d, h, motivo):
    previos = sum(1 for b in d["bloqueos"] if _mismo(b, h)); mins = DURACIONES[min(previos, 2)]
    hasta = (datetime.datetime.now() + datetime.timedelta(minutes=mins)).isoformat(timespec="seconds")
    b = {"id": next_id(d, "bloqueos"), "dev_hash": h["dev_hash"], "ip_hash": h["ip_hash"], "ip_mask": h["ip_mask"], "motivo": motivo,
         "minutos": mins, "desde": now(), "hasta": hasta, "activo": 1, "nivel": previos + 1,
         "rep_id": max([r["id"] for r in d["reportes"]] or [0])}   # el conteo de reclamos empieza de nuevo después de cada bloqueo
    d["bloqueos"].append(b); return b
def _msg(b): return f"Tu dispositivo quedó bloqueado hasta las {b['hasta'][11:16]} por reclamos reiterados. Si creés que es un error, consultá a la administración."
def controlar(d, h):
    """Se llama antes de guardar un reclamo. Si corresponde, crea el bloqueo y lanza Bloqueado."""
    b = activo(d, h)
    if b: raise Bloqueado(_msg(b))
    corte = max([b.get("rep_id", 0) for b in d["bloqueos"] if _mismo(b, h)] or [0])   # tras un bloqueo, el conteo empieza de nuevo
    mios = [r for r in d["reportes"] if _mismo(r, h) and r["id"] > corte]
    n10 = sum(1 for r in mios if r["creado_en"] >= _hace(10)); n24 = sum(1 for r in mios if r["creado_en"] >= _hace(1440))
    if n10 >= 3 or n24 >= 10:
        raise Bloqueado(_msg(_bloquear(d, h, "Más de 3 reclamos en 10 minutos" if n10 >= 3 else "Más de 10 reclamos en 24 horas")))
def falta(d, r):
    """Un reclamo quedó «no constatado»: si el mismo autor suma 2 en 24 h, se bloquea."""
    if not r.get("dev_hash"): return
    h = {"dev_hash": r["dev_hash"], "ip_hash": r["ip_hash"], "ip_mask": r.get("ip_mask", "")}
    n = sum(1 for x in d["reportes"] if x["estado"] == "no_constatado" and _mismo(x, h) and x["creado_en"] >= _hace(1440))
    if n >= 2 and not activo(d, h): _bloquear(d, h, "2 reclamos no constatados en 24 horas")
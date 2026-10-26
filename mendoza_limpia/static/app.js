const $ = id => document.getElementById(id); const U = { aj: false, rj: false, sel: [] }; let E = null, rol = null, modo = null, last = "";
const toast = m => { const t = $("toast"); t.textContent = m; t.className = "on"; setTimeout(() => t.className = "", 3200) };
async function api(p, b) { const r = await fetch("/api" + p, { method: b === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json" }, body: b === undefined ? undefined : JSON.stringify(b) }); const j = await r.json(); if (!r.ok) { toast("⚠ " + (j.error || "Error")); throw new Error(j.error) } return j }
async function act(p, b) { try { E = await api(p, b); U.aj = U.rj = false; draw() } catch (e) { } }
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const hora = s => (s || "").slice(11, 16), pill = (n, t) => `<span class="pill ${n}">${(t || n).replace("_", " ").toUpperCase()}</span>`;
const color = n => n === "alto" ? "hi" : n === "medio" ? "md" : "lo";
const NM = { vecino: "📝 Reclamo", operador: "🧑‍💼 Operador de Higiene Urbana", supervisor: "🛡️ Supervisor", cuadrilla: "🚛 Cuadrilla", ureclamo: "📝 Hacer un reclamo", recolector: "🕒 Horario del recolector" }; function togg(i) { const z = E.propuesta.ruta[i], k = U.sel.indexOf(z); k >= 0 ? U.sel.splice(k, 1) : U.sel.push(z); draw() }
function go(r) { rol = r; draw(); scrollTo(0, 0) }
function logBox() { return `<div class="card"><h2>📜 Registro de mensajes del sistema</h2><div class="log">${E.log.map(l => `<div><b>${l.mensaje || "·"}</b> · ${hora(l.creado_en)} · <b>${esc(l.actor)}</b>: ${esc(l.texto)}</div>`).join("") || "<span class='mu'>Todavía no hay mensajes.</span>"}</div></div>` }
function riesgo() { return `<div class="tw"><table><tr><th>Zona</th><th>Puntaje</th><th></th><th>Riesgo</th></tr>${E.zonas.map(z => `<tr><td>${esc(z.nombre)}</td><td>${z.puntaje.toFixed(2)}</td><td><div class="bar"><i style="width:${z.puntaje * 100}%;background:var(--${color(z.nivel)})"></i></div></td><td>${pill(z.nivel)}</td></tr>`).join("")}</table></div><p class="mu">Puntaje = histórico del turno × (1 + clima) + eventos + reportes validados. Reglas simples y explicables, no un modelo entrenado.</p>` }
function repList(f, acc) { const l = E.reportes.filter(f); return l.map(r => `<div class="rep"><span class="t"><b>#${r.id} · ${esc(r.zona)}</b>${r.tipo ? " · " + esc(r.tipo) : ""} — ${esc(r.descripcion)}${r.direccion ? " (" + esc(r.direccion) + ")" : ""}<br><span class="mu">${r.origen} · ${hora(r.creado_en)}${r.comentario ? " · " + esc(r.comentario) : ""}</span></span>${pill(r.estado)}${acc && r.estado === "pendiente" ? `<button class="b ok" onclick="act('/reportes/${r.id}/validar',{})">Validar</button><button class="b gh" onclick="act('/reportes/${r.id}/descartar',{})">Descartar</button>` : ""}</div>`).join("") }
function home() {
    const k = E.kpis; return `<div class="hero"><h1>Anticipamos dónde se va a acumular la basura</h1><p>El sistema predice el riesgo por zona y turno y propone la ruta. Los camiones los despacha siempre una persona.</p><div class="stats"><div class="stat"><b>${k.total}</b><span>reportes guardados</span></div><div class="stat"><b>${k.pendientes}</b><span>pendientes de validar</span></div><div class="stat"><b>${k.validados}</b><span>validados</span></div></div></div>
<h2>¿Quién ingresa?</h2><div class="grid">
<button class="role" onclick="go('vecino')"><span class="ic">📝</span><b>Reclamo</b><small>Cargá un reclamo de desborde (vecino o inspector).</small></button>
<button class="role" onclick="go('operador')"><span class="ic">🧑‍💼</span><b>Operador de Higiene Urbana</b><small>Valida reportes, decide la ruta y despacha.</small></button>
<button class="role" onclick="go('supervisor')"><span class="ic">🛡️</span><b>Supervisor</b><small>Recalibración semanal y escalada.</small></button>
<button class="role" onclick="go('cuadrilla')"><span class="ic">🚛</span><b>Cuadrilla de recolección</b><small>Recorre la ruta y reporta lo que ve.</small></button></div><p class="mu">Los agentes de software (Predictor y Planificador) no tienen ingreso: trabajan por detrás y le hablan al Operador.</p>`+ logBox()
}
function vecino() {
    return `<div class="card"><h2>🏘️ Reportar un desborde</h2><p class="mu">El reporte se guarda en el archivo JSON y aparece en el panel del Operador. Es un dato: no ordena ninguna recolección hasta que el Operador lo valide.</p>
<div class="row"><select id="vo"><option value="vecino">Soy vecino</option><option value="inspector">Soy inspector</option></select><select id="vz">${E.zonas.map(z => `<option>${esc(z.nombre)}</option>`).sort().join("")}</select><input id="vt" placeholder="¿Qué viste?" maxlength="300" style="flex:1;min-width:220px"><button class="b" onclick="enviar()">Enviar reporte</button></div></div>
<div class="card"><h2>📋 Últimos reportes</h2>${repList(() => true, false) || "<span class='mu'>Sin reportes.</span>"}</div>`
}
function enviar() { const d = $("vt").value.trim(); if (!d) return toast("⚠ Contá qué viste"); act("/reportes", { zona: $("vz").value, descripcion: d, origen: $("vo").value }).then(() => toast("✔ Reporte guardado. Lo revisa el Operador.")) }
function decPanel() {
    const p = E.propuesta;
    if (p.estado === "despachada") return `<p>🚛 <b>Ruta despachada</b> por ${p.decidido_por}. La cuadrilla ya recibió la orden.</p><button class="b gh" onclick="act('/turno/nuevo',{})">Preparar un nuevo turno</button>`;
    if (p.estado === "rechazada") return `<p>⛔ <b>Propuesta rechazada.</b> Se mantiene la ruta habitual. Motivo: «${esc(p.motivo)}»</p><div class="row"><button class="b gh" onclick="act('/propuesta/revisar',{})">Volver a revisar</button><button class="b" onclick="act('/turno/nuevo',{})">Preparar un nuevo turno</button></div>`;
    if (p.estado !== "pendiente") return `<p>✅ Decisión: <b>${p.estado}</b> (${p.decidido_por}). Ruta: ${p.ruta_final.join(" → ")}</p><button class="b ok" onclick="act('/despachar',{actor:'${p.decidido_por}'})">🚛 Despachar cuadrilla <span class="n">N2</span></button>`;
    return ""
}
function operador() {
    const p = E.propuesta, c = E.contexto, alt = E.zonas.filter(z => z.nivel === "alto").map(z => z.nombre), d = E.despacho;
    let dec = decPanel();
    if (p.estado === "pendiente") dec = `<h3>Decidí sobre la propuesta <span class="n">N1</span></h3><div class="row"><button class="b ok" onclick="act('/propuesta/decidir',{decision:'aprobada',actor:'operador'})">✔ Aprobar</button><button class="b gh" onclick="U.aj=!U.aj;U.rj=false;U.sel=[];draw()">✎ Ajustar</button><button class="b no" onclick="U.rj=!U.rj;U.aj=false;draw()">✖ Rechazar</button></div>
    ${U.aj ? `<p class="mu" style="margin-top:10px">Tocá las zonas en el orden en que querés recorrerlas. Las que no toques quedan fuera.</p><div class="row">${p.ruta.map((z, i) => { const n = U.sel.indexOf(z); return `<button class="b ${n >= 0 ? "ok" : "gh"}" onclick="togg(${i})">${n >= 0 ? (n + 1) + ". " : ""}${esc(z)}</button>` }).join("")}<button class="b" onclick="act('/propuesta/decidir',{decision:'ajustada',actor:'operador',zonas:U.sel})">Confirmar ajuste</button></div>` : ""}
    ${U.rj ? `<div class="row" style="margin-top:10px"><input id="mt" placeholder="Motivo del rechazo" style="flex:1;min-width:220px"><button class="b no" onclick="act('/propuesta/decidir',{decision:'rechazada',actor:'operador',motivo:$('mt').value})">Confirmar rechazo</button></div>` : ""}
 <p><button class="b" disabled style="margin-top:12px">🚛 Despachar (bloqueado hasta decidir)</button></p><p><button class="b gh" onclick="act('/propuesta/escalar',{})">⏱ Simular: pasaron 2 horas sin respuesta</button></p>${p.escalada ? `<p class="mu">Recordatorio enviado y pedido de decisión al Supervisor.</p>` : ""}`;
    return `<div class="steps"><span>1 Datos</span><span>2 Mapa</span><span>3 Reportes</span><span>4 Ruta</span><span>5 Resultado</span></div>
<div class="card"><h2>🌦 1 · Datos del día (Agente 1 — Predictor)</h2><div class="row">Clima <select onchange="act('/contexto',{clima:this.value,turno:${c.turno},evento:${!!c.evento}})">${["normal", "lluvia", "calor"].map(x => `<option ${x === c.clima ? "selected" : ""}>${x}</option>`).join("")}</select>Turno <select onchange="act('/contexto',{clima:'${c.clima}',turno:+this.value,evento:${!!c.evento}})"><option value="0">Mañana</option><option value="1" ${c.turno ? "selected" : ""}>Tarde</option></select><label><input type="checkbox" ${c.evento ? "checked" : ""} onchange="act('/contexto',{clima:'${c.clima}',turno:${c.turno},evento:this.checked})"> Evento municipal mañana</label></div></div>
<div class="card"><h2>🗺 2 · Mapa de riesgo por zona</h2>${alt.length ? `<div class="alert"><b>🚨 Alerta temprana:</b> riesgo alto en ${alt.join(", ")}. Van primero en la ruta.</div>` : `<p class="mu">Sin zonas de riesgo alto.</p>`}${riesgo()}</div>
<div class="card"><h2>📥 3 · Reportes de vecinos e inspectores (archivo JSON)</h2>${repList(r => r.estado === "pendiente", true) || "<span class='mu'>No hay reportes pendientes.</span>"}<h3>Ya revisados</h3>${repList(r => r.estado !== "pendiente", false) || "<span class='mu'>Todavía ninguno.</span>"}<p class="mu">Un reporte validado suma al mapa de riesgo; si la ruta aún no salió, hay que decidir de nuevo.</p></div>
<div class="card"><h2>🧭 4 · Ruta propuesta (Agente 2 — Planificador)</h2><div class="route">${p.ruta.map((z, i) => `<span>${i + 1}. ${esc(z)}</span>`).join("")}</div><p class="mu">Propone, no asigna camiones. Flota y turnos: 3 camiones, 2 turnos (datos de prueba).</p>${dec}</div>
${d && d.resultado_en ? `<div class="card"><h2>📊 5 · Resultado real de la calle</h2><p>Contenedores levantados: <b>${d.contenedores}</b> · Desbordes vistos: <b>${d.desbordes}</b></p></div>` : ""}` + logBox()
}
function supervisor() {
    const r = E.recal, p = E.propuesta;
    return `<div class="card"><h2>📈 Control semanal del modelo</h2><p>Precisión de la semana: <b>${r.precision}%</b> · umbral mínimo <b>75%</b></p>
 ${r.estado === "propuesta" ? `<div class="alert"><b>El Agente 1 propone recalibrar</b> antes de seguir priorizando rutas con el modelo <span class="n">11</span></div><div class="row"><button class="b ok" onclick="act('/recalibracion/decidir',{decision:'aceptada'})">Aceptar recalibración</button><button class="b no" onclick="act('/recalibracion/decidir',{decision:'rechazada'})">Rechazar</button></div>` : `<p>Decisión del Supervisor: <b>${r.estado}</b>. El modelo no se cambia solo: lo decide una persona.</p><button class="b gh" onclick="act('/recalibracion/semana',{})">Simular nueva semana</button>`}
 <p class="mu">Cobertura de desbordes: ${r.cobertura}% (mínimo 70%) · Km sin recolección: ${r.km_var}% (meta −15% a los 2 meses).</p></div>
<div class="card"><h2>⏱ Escalada: el Operador no respondió</h2>${p.escalada && p.estado === "pendiente" ? `<div class="alert"><b>Decisión pendiente</b> <span class="n">N4</span><br>Ruta propuesta: ${p.ruta.join(" → ")}</div><div class="row"><button class="b ok" onclick="act('/propuesta/decidir',{decision:'aprobada',actor:'supervisor'})">Aprobar ruta</button><button class="b no" onclick="act('/propuesta/decidir',{decision:'rechazada',actor:'supervisor',motivo:'Sin autorización a tiempo'})">Rechazar y mantener ruta habitual</button></div><p class="mu">Si nadie responde, no se despacha nada.</p>` : `<p class="mu">No hay decisiones escaladas.</p>`}
 ${p.escalada && ["aprobada", "ajustada"].includes(p.estado) ? `<button class="b ok" onclick="act('/despachar',{actor:'supervisor'})">🚛 Ordenar salida de la cuadrilla</button>` : ""}</div>` + logBox()
}
function cuadrilla() {
    const p = E.propuesta, d = E.despacho;
    const ok = p.estado === "despachada" && d;
    return `<div class="card"><h2>🚛 Mi recorrido</h2>${ok ? `<div class="route">${p.ruta_final.map((z, i) => `<span>${i + 1}. ${esc(z)}</span>`).join("")}</div>${!d.salida_confirmada_en ? `<button class="b ok" onclick="act('/cuadrilla/salida',{})">Confirmar salida</button>` : ""}
 ${d.salida_confirmada_en && !d.resultado_en ? (E.verificar.length ? `<h3>Verificar los reclamos en la calle</h3>${E.verificar.map(verif).join("")}<p><button class="b" ${E.verificar.every(listo) ? "" : "disabled"} onclick="enviarRes()">Enviar resultado al Operador</button></p>` : `<h3>Informar resultado</h3><div class="row">Contenedores levantados <input id="rc" type="number" min="0" value="${p.ruta_final.length * 6}" style="width:90px">Desbordes vistos <input id="rd" type="number" min="0" value="1" style="width:80px"><button class="b" onclick="act('/cuadrilla/resultado',{contenedores:+$('rc').value,desbordes:+$('rd').value})">Enviar al Operador</button></div>`) : ""}${d.resultado_en ? "<p>✅ Resultado enviado al Operador.</p>" : ""} <p class="mu">La cuadrilla no cambia la ruta ni saltea zonas por su cuenta: cualquier cambio lo autoriza el Operador.</p>` : `<p class="mu">Todavía no hay una ruta despachada. Cuando el Operador la apruebe y despache, aparece acá.</p>`}</div>` + logBox()
}
function modoSet(m) { modo = m; rol = null; draw(); scrollTo(0, 0) }
function landing() {
    return `<div class="hero"><h1>Mendoza Limpia</h1><p>Anticipamos dónde se va a acumular la basura para que la recolección llegue antes de que sea un problema.</p></div>
<h2>¿Cómo ingresás?</h2><div class="grid">
<button class="role" onclick="modoSet('usuario')"><span class="ic">👤</span><b>Usuario</b><small>Hacé un reclamo o consultá cuándo pasa el recolector por tu casa.</small></button>
<button class="role" onclick="modoSet('operador')"><span class="ic">🧑‍💼</span><b>Operador</b><small>Reclamos, rutas, supervisión y cuadrilla.</small></button></div>`}
function usuario() {
    return `<div class="hero"><h1>Hola 👋</h1><p>Contanos qué pasa en tu barrio o consultá cuándo pasa el recolector.</p></div><div class="grid">
<button class="role" onclick="go('ureclamo')"><span class="ic">📝</span><b>Hacer un reclamo</b><small>Desborde de basura, contenedor roto, basural u otro.</small></button>
<button class="role" onclick="go('recolector')"><span class="ic">🕒</span><b>¿Cuándo pasa el recolector?</b><small>Ingresá tu dirección y mirá el horario.</small></button></div>`}
const TIPOS = ["Desborde de basura", "Contenedor roto o faltante", "Basural / residuos en la calle", "Recolección que no pasó", "Otro"];
const zonasOrd = () => E.zonas.map(z => z.nombre).sort().map(n => `<option>${esc(n)}</option>`).join("");
function ureclamo() {
    return `<div class="card"><h2>📝 Hacer un reclamo</h2><p class="mu">Tu reclamo llega al panel del Operador de Higiene Urbana, que lo revisa y lo valida antes de usarlo.</p>
<div class="row"><select id="ut">${TIPOS.map(t => `<option>${t}</option>`).join("")}</select><select id="uz">${zonasOrd()}</select></div>
<div class="row" style="margin-top:8px"><input id="ud" placeholder="Dirección o referencia (ej: San Martín 1200)" style="flex:1;min-width:220px"><input id="ux" placeholder="Contanos qué pasa" maxlength="300" style="flex:2;min-width:220px"></div>
<p><button class="b" onclick="uenviar()">Enviar reclamo</button></p></div>
<div class="card"><h2>📋 Últimos reclamos</h2>${repList(() => true, false) || "<span class='mu'>Todavía no hay reclamos.</span>"}</div>`
}
function uenviar() { const x = $("ux").value.trim(); if (!x) return toast("⚠ Contanos qué pasa"); act("/reportes", { zona: $("uz").value, tipo: $("ut").value, direccion: $("ud").value.trim(), descripcion: x, origen: "vecino" }).then(() => toast("✔ Reclamo enviado. Lo revisa el Operador.")) }
let R = null;
function recolector() {
    return `<div class="card"><h2>🕒 ¿Cuándo pasa el recolector por mi cuadra?</h2><p class="mu">Ingresá tu calle y altura. Si no la reconocemos, elegí tu zona en la lista. Horarios de prueba.</p>
<div class="row"><input id="rq" placeholder="Ej: San Martín 1200" value="${R ? esc(R.q) : ""}" style="flex:1;min-width:220px"><select id="rz"><option value="">Detectar por dirección</option>${zonasOrd()}</select><button class="b" onclick="consultar()">Consultar</button></div></div>${R ? resultadoR() : ""}`
}
async function consultar() { const q = $("rq").value.trim(); try { R = Object.assign({ q }, await api("/recolector", { direccion: q, zona: $("rz").value })); draw() } catch (e) { R = null } }
function resultadoR() {
    return `<div class="card"><h2>📍 ${esc(R.zona)}</h2><p class="mu">${R.detectada ? "Zona detectada por tu dirección." : "Zona elegida por vos."}</p>
${R.pasos.map(p => `<div class="rep"><span class="t"><b>${p.hora} h</b> · ${esc(p.turno)}</span><span class="pill ${p.paso ? "bajo" : "medio"}">${p.paso ? "YA PASÓ" : "EN " + p.faltan}</span></div>`).join("")}
<div class="alert" style="margin-top:12px">${esc(R.mensaje)}</div>${R.ruta_hoy ? "<p>🚛 Hoy hay una ruta despachada que incluye tu zona.</p>" : ""}</div>`
}
let Q = {};
const MOTIVOS = ["Falta de tiempo", "Falta de espacio en el camión", "Acceso bloqueado", "Zona fuera de la ruta"];
function qs(id, k, v) { (Q[id] = Q[id] || {})[k] = v; if (k === "habia" && v && Q[id].cuantos == null) Q[id].cuantos = 1; draw() }
function listo(r) { const q = Q[r.id] || {}; return (q.paso === true && q.habia != null) || (q.paso === false && !!q.motivo) }
const sn = (t, on, fn) => `<button class="b ${on ? "ok" : "gh"}" onclick="${fn}">${t}</button>`;
function verif(r) {
    const q = Q[r.id] || {}, lugar = esc(r.direccion || r.zona);
    return `<div class="rep" style="display:block"><b>#${r.id} · ${esc(r.zona)}</b>${r.tipo ? " · " + esc(r.tipo) : ""}<br><span class="mu">${esc(r.descripcion)}</span>
 <p><b>¿Pasaste por ${lugar}?</b></p><div class="row">${sn("Sí", q.paso === true, `qs(${r.id},'paso',true)`)}${sn("No", q.paso === false, `qs(${r.id},'paso',false)`)}</div>
 ${q.paso === true ? `<p><b>¿Había desborde?</b></p><div class="row">${sn("Sí", q.habia === true, `qs(${r.id},'habia',true)`)}${sn("No", q.habia === false, `qs(${r.id},'habia',false)`)}</div>` : ""}
 ${q.paso === true && q.habia === true ? `<p><b>¿Cuántos contenedores levantaron?</b> <input type="number" min="0" value="${q.cuantos || 1}" style="width:80px" onchange="qs(${r.id},'cuantos',+this.value)"></p>` : ""}
 ${q.paso === false ? `<p><b>¿Por qué no pasaste?</b></p><div class="row">${MOTIVOS.map(m => sn(m, q.motivo === m, `qs(${r.id},'motivo','${m}')`)).join("")}</div>` : ""}</div>`
}
function enviarRes() { act("/cuadrilla/resultado", { contenedores: 0, desbordes: 0, verificaciones: E.verificar.map(r => ({ id: r.id, ...Q[r.id] })) }).then(() => { Q = {} }) }

const V = { home, vecino, operador, supervisor, cuadrilla, ureclamo, recolector };
function draw() {
    if (!E) return;
    const lk = (t, f) => `<a href="#" onclick="${f};return false">${t}</a>`;
    $("who").innerHTML = !modo ? "" : rol ? `${NM[rol]} · ${lk("Volver", "go(null)")} · ${lk("Pantalla principal", "modoSet(null)")}` : `${modo === "usuario" ? "👤 Usuario" : "🧑‍💼 Operador"} · ${lk("Pantalla principal", "modoSet(null)")}`;
    $("app").innerHTML = !modo ? landing() : rol ? V[rol]() : modo === "usuario" ? usuario() : home(); last = JSON.stringify(E)
}
$("reset").onclick = async e => { e.preventDefault(); if (confirm("¿Reiniciar la demo y borrar los datos guardados?")) { E = await api("/demo/reset", {}); rol = null; draw() } };
async function poll() { const a = document.activeElement; if (a && ["INPUT", "SELECT"].includes(a.tagName)) return; try { const n = await api("/estado"); if (JSON.stringify(n) !== last) { E = n; draw() } } catch (e) { } }
(async () => { E = await api("/estado"); draw(); setInterval(poll, 2500) })();

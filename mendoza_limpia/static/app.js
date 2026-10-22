const $ = id => document.getElementById(id); const U = { aj: false, rj: false, sel: [] }; let E = null, rol = null, last = "";
const toast = m => { const t = $("toast"); t.textContent = m; t.className = "on"; setTimeout(() => t.className = "", 3200) };
async function api(p, b) { const r = await fetch("/api" + p, { method: b === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json" }, body: b === undefined ? undefined : JSON.stringify(b) }); const j = await r.json(); if (!r.ok) { toast("⚠ " + (j.error || "Error")); throw new Error(j.error) } return j }
async function act(p, b) { try { E = await api(p, b); U.aj = U.rj = false; draw() } catch (e) { } }
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const hora = s => (s || "").slice(11, 16), pill = (n, t) => `<span class="pill ${n}">${(t || n).toUpperCase()}</span>`;
const color = n => n === "alto" ? "hi" : n === "medio" ? "md" : "lo";
const NM = { vecino: "🏘️ Vecino / inspector", operador: "🧑‍💼 Operador de Higiene Urbana", supervisor: "🛡️ Supervisor", cuadrilla: "🚛 Cuadrilla" };
function togg(i) { const z = E.propuesta.ruta[i], k = U.sel.indexOf(z); k >= 0 ? U.sel.splice(k, 1) : U.sel.push(z); draw() }
function go(r) { rol = r; draw(); scrollTo(0, 0) }
function logBox() { return `<div class="card"><h2>📜 Registro de mensajes del sistema</h2><div class="log">${E.log.map(l => `<div><b>${l.mensaje || "·"}</b> · ${hora(l.creado_en)} · <b>${esc(l.actor)}</b>: ${esc(l.texto)}</div>`).join("") || "<span class='mu'>Todavía no hay mensajes.</span>"}</div></div>` }
function riesgo() { return `<div class="tw"><table><tr><th>Zona</th><th>Puntaje</th><th></th><th>Riesgo</th></tr>${E.zonas.map(z => `<tr><td>${esc(z.nombre)}</td><td>${z.puntaje.toFixed(2)}</td><td><div class="bar"><i style="width:${z.puntaje * 100}%;background:var(--${color(z.nivel)})"></i></div></td><td>${pill(z.nivel)}</td></tr>`).join("")}</table></div><p class="mu">Puntaje = histórico del turno × (1 + clima) + eventos + reportes validados. Reglas simples y explicables, no un modelo entrenado.</p>` }
function repList(f, acc) { const l = E.reportes.filter(f); return l.map(r => `<div class="rep"><span class="t"><b>#${r.id} · ${esc(r.zona)}</b> — ${esc(r.descripcion)}<br><span class="mu">${r.origen} · ${hora(r.creado_en)}</span></span>${pill(r.estado)}${acc && r.estado === "pendiente" ? `<button class="b ok" onclick="act('/reportes/${r.id}/validar',{})">Validar</button><button class="b gh" onclick="act('/reportes/${r.id}/descartar',{})">Descartar</button>` : ""}</div>`).join("") }
function home() {
    const k = E.kpis; return `<div class="hero"><h1>Anticipamos dónde se va a acumular la basura</h1><p>El sistema predice el riesgo por zona y turno y propone la ruta. Los camiones los despacha siempre una persona.</p><div class="stats"><div class="stat"><b>${k.total}</b><span>reportes guardados</span></div><div class="stat"><b>${k.pendientes}</b><span>pendientes de validar</span></div><div class="stat"><b>${k.validados}</b><span>validados</span></div></div></div>
<h2>¿Quién ingresa?</h2><div class="grid">
<button class="role" onclick="go('vecino')"><span class="ic">🏘️</span><b>Vecino / inspector</b><small>Avisa de un desborde en la vía pública.</small></button>
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
 ${d.salida_confirmada_en && !d.resultado_en ? `<h3>Informar resultado</h3><div class="row">Contenedores levantados <input id="rc" type="number" min="0" value="${p.ruta_final.length * 6}" style="width:90px">Desbordes vistos <input id="rd" type="number" min="0" value="1" style="width:80px"><button class="b" onclick="act('/cuadrilla/resultado',{contenedores:+$('rc').value,desbordes:+$('rd').value})">Enviar al Operador</button></div>` : ""}${d.resultado_en ? "<p>✅ Resultado enviado al Operador. ¡Buen trabajo!</p>" : ""}
 <p class="mu">La cuadrilla no cambia la ruta ni saltea zonas por su cuenta: cualquier cambio lo autoriza el Operador.</p>`: `<p class="mu">Todavía no hay una ruta despachada. Cuando el Operador la apruebe y despache, aparece acá.</p>`}</div>` + logBox()
}
const V = { home, vecino, operador, supervisor, cuadrilla };
function draw() { if (!E) return; $("who").innerHTML = rol ? `${NM[rol]} · <a href="#" onclick="go(null);return false">Cambiar de rol</a>` : ""; $("app").innerHTML = V[rol || "home"](); last = JSON.stringify(E) }
$("reset").onclick = async e => { e.preventDefault(); if (confirm("¿Reiniciar la demo y borrar los datos guardados?")) { E = await api("/demo/reset", {}); rol = null; draw() } };
async function poll() { const a = document.activeElement; if (a && ["INPUT", "SELECT"].includes(a.tagName)) return; try { const n = await api("/estado"); if (JSON.stringify(n) !== last) { E = n; draw() } } catch (e) { } }
(async () => { E = await api("/estado"); draw(); setInterval(poll, 2500) })();

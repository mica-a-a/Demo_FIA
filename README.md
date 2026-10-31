# ♻ Mendoza Limpia
**Sistema de prevención de acumulación de residuos urbanos** · MVP para hackatón
Proyecto de Innovación — Fundamentos de Inteligencia Artificial · Universidad Champagnat · 2026
Grupo 2: Bazán Franco, Gorri Juan, Le Donne Micaela, Molina Agostina, Nievas Milagros

> **Anticipamos dónde va a acumularse la basura en Mendoza, para que la recolección llegue antes de que se convierta en un problema.**
> El sistema propone; una persona decide. Despachar los camiones es la única acción irreversible y **nunca** la ejecuta el software.

---

## 1. El problema
En la Ciudad de Mendoza los contenedores se desbordan en algunas zonas mientras los camiones pasan por otras casi vacías. La recolección responde a rutas y frecuencias fijas, no a la acumulación real, que varía por zona, día, clima y eventos.

- **Evidencia:** reclamos vecinales documentados en medios locales (MDZ Online, Diario Los Andes) por acumulación imprevista de basura en el microcentro.
- **Quién lo sufre:** el vecino (basura en la vía pública), el trabajador de recolección (recorridos ineficientes) y el área de Higiene Urbana (gasta combustible, horas de trabajo y vehículos sin predicción).
- **Alternativa sin IA (considerada y descartada):** aumentar la frecuencia en toda la ciudad sin diferenciar zonas, o sumar inspección visual manual. Ambas son más caras y no anticipan.

## 2. La solución
Dos agentes de software y personas que conservan la decisión final.

| Agente / actor | Tipo | Qué hace |
|---|---|---|
| **Agente 1 — Predictor de Acumulación** | Software | Calcula el riesgo por zona y turno (alto/medio/bajo) con datos históricos, clima, eventos y reclamos validados. |
| **Agente 2 — Planificador de Rutas** | Software | Propone ruta y frecuencia por turno, con las zonas de mayor riesgo primero. No asigna camiones. |
| **Usuario** (sin cuenta) | Persona | Hace reclamos (desborde, contenedor roto, basural, etc.) y consulta cuándo pasa el recolector por su cuadra. |
| **Operador** | Persona | Valida reclamos, aprueba/ajusta/rechaza la ruta, despacha, y desde la cuadrilla verifica los reclamos en la calle. |
| **Admin** (cumple el rol de Supervisor) | Persona | Decide la recalibración semanal, resuelve cuando el Operador no responde, y gestiona bloqueos. |
| **Desarrollador** | Persona | Panel técnico, datos del sistema y reinicio de la demo. |

**Propuesta de valor:** reducir kilómetros recorridos sin recolección efectiva (hipótesis: −45 % en el primer semestre) usando datos públicos de la Ciudad combinados con clima y calendario, sin depender de sensores costosos.

## 3. Reglas no delegables (se cumplen también en el backend)
| Marca | Decisión humana | Cómo lo hace cumplir el sistema |
|---|---|---|
| **N1** | Aprobar, ajustar o rechazar la ruta | `models.decidir` solo acepta personas autorizadas; ningún agente decide. |
| **N2** | Despachar a la cuadrilla | `models.despachar` rechaza (HTTP 409) si no hay una ruta aprobada por una persona. |
| **N3** | Resolver contradicciones entre agentes | La propuesta llega marcada al Operador; ningún agente impone su versión. |
| **N4** | Decidir cuando el Operador no responde | El Admin solo puede decidir si hubo escalada; si nadie responde, **no se despacha nada**. |

El silencio nunca cuenta como permiso. La decisión no delegable del canvas es la **reasignación de personal / despacho de la cuadrilla**; las multas quedan fuera del alcance del sistema.

## 4. Roles, login y permisos
El **Usuario** no tiene cuenta. El **personal** (operador, admin, desarrollador) ingresa con usuario y contraseña. Las contraseñas se guardan cifradas (PBKDF2) y la sesión viaja en una cookie `HttpOnly`. **Los permisos se controlan en el servidor**, no solo ocultando botones: cada ruta de la API declara qué roles la pueden usar.

| Rol | Qué ve | Qué puede hacer |
|---|---|---|
| Usuario (sin login) | Reclamos, horario del recolector | Crear reclamos, consultar horarios |
| Operador | Panel del Operador y Cuadrilla | Cambiar datos del día, validar/descartar reclamos, decidir ruta (N1), despachar (N2), confirmar salida, verificar reclamos en la calle |
| Admin | Supervisión, Usuarios y bloqueos | Recalibración, decidir si hubo escalada (N4), ordenar la salida en ese caso, desbloquear dispositivos |
| Desarrollador | Panel técnico | Ver el resumen del sistema y reiniciar la demo |

**Credenciales de demo** (están en `app/db.py`, deben cambiarse en una versión real): `operador / operador123` · `admin / admin123` · `dev / dev123`.

## 5. Control de abuso y privacidad
Para detectar quién hace reclamos reiterados (posiblemente falsos) el sistema registra, **sin pedir cuenta**:
- la **dirección IP** (la ve el servidor en cada pedido),
- un **identificador de dispositivo/navegador** (aleatorio, guardado en el navegador) y el *User-Agent*.

**No se usa IMEI ni máscara de red**: desde una página web el navegador no tiene acceso al IMEI (es un dato de celulares y de apps nativas), y la máscara describe la red local, no a la persona.

**Regla de bloqueo:**
- Más de **3 reclamos en 10 minutos** o más de **10 en 24 horas** → bloqueo de **30 min**; reincidencia → **1 h**; luego **24 h**.
- Cada reclamo **«no constatado»** cuenta como falta: **2 en 24 h** también bloquean.
- Tras un bloqueo el conteo empieza de nuevo. El **Admin puede desbloquear**.
- Se identifica al autor por dispositivo, o por IP **salvo en localhost** (en una demo local todos comparten `127.0.0.1`). Una IP sola no alcanza: varias personas comparten IP en wifi y celulares.

**Privacidad (Ley 25.326):** IP y dispositivo se guardan **hasheados**; el Admin solo ve una IP parcial (`190.12.x.x`). El formulario avisa que se registran. **Límites:** quien borra los datos del navegador o usa una ventana de incógnito obtiene otro identificador de dispositivo.

## 6. Ciclo de vida de un reclamo
```
Usuario reclama ─▶ pendiente ─▶ (Operador) validado ─▶ suma al riesgo de su zona
                      │                │
                      │                └▶ si la zona está en la ruta despachada, la cuadrilla verifica:
                      └▶ descartado        ¿Pasaste? Sí → ¿Había desborde? Sí → ¿Cuántos contenedores? → RESUELTO
                                                             No → NO CONSTATADO («desborde inexistente»)
                                                     No → motivo (falta de tiempo, de espacio, acceso bloqueado,
                                                          zona fuera de la ruta) → vuelve a PENDIENTE
```
El Operador puede **ajustar** la ruta: las zonas se recorren **en el orden en que las selecciona**, y las que no selecciona quedan fuera.

## 7. Arquitectura MVC
```
 Navegador (Vista)  ──HTTP/JSON──▶  server.py (enrutador + sesión + IP/dispositivo)
 static/index.html                       │
 static/app.js, style.css                ▼
                                  app/controllers.py   (Controlador: rutas y permisos por rol)
                                         │
                                         ▼
          app/models.py · predictor.py · recorridos.py · security.py · auth.py   (Modelo + agentes)
                                         │
                                         ▼
                              app/db.py ── archivo JSON (data/datos.json)
```
- **Modelo:** reglas de negocio, agentes, control de abuso y acceso a datos. Aquí se hacen cumplir N1–N4.
- **Vista (`static/`):** pantalla principal (Usuario / Personal), login y un panel por rol. Se actualiza sola cada 2,5 s: un reclamo del Usuario aparece en el panel del Operador.
- **Controlador (`app/controllers.py`):** traduce cada endpoint a una operación del modelo y valida el rol.
- **Sin dependencias externas:** solo la biblioteca estándar de Python 3.8+.

## 8. Almacenamiento de datos (archivo JSON)
Los datos viven en **`data/datos.json`**, un archivo de texto legible. Se crea solo la primera vez a partir de los **datos de prueba (mock)** de `data/datos_mock.json`; si el archivo es de una versión anterior, el sistema le agrega solo los usuarios y bloqueos. Cada cambio se escribe de forma atómica y con bloqueo. **«Reiniciar demo»** (solo Desarrollador) restaura los datos de prueba.

| Colección | Para qué sirve | Campos principales |
|---|---|---|
| `zonas` | Catálogo de zonas con su histórico | `nombre`, `hist_manana`, `hist_tarde`, `afectada_evento` |
| `contexto` | Datos del día | `clima`, `turno`, `evento` |
| `reportes` | Reclamos (mensaje 0) | `zona_id`, `tipo`, `direccion`, `descripcion`, `estado` (pendiente/validado/descartado/resuelto/no_constatado), `comentario`, `levantados`, `ip_hash`, `dev_hash`, `ip_mask`, `ua`, fechas |
| `propuestas` | Ruta propuesta y decisión humana (N1) | `ruta`, `estado`, `ruta_final` (en el orden elegido), `motivo`, `decidido_por`, `escalada` |
| `despachos` | Salida y resultado (N2, mensajes 8–10) | `propuesta_id`, `ordenado_por`, `salida_confirmada_en`, `contenedores`, `desbordes`, `resultado_en` |
| `recalibraciones` | Control semanal del modelo (mensajes 11–12) | `precision`, `cobertura`, `km_var`, `estado`, `decidido_por` |
| `usuarios` | Personal con acceso | `usuario`, `nombre`, `rol`, `salt`, `hash` (contraseña cifrada) |
| `bloqueos` | Control de abuso | `dev_hash`, `ip_hash`, `motivo`, `minutos`, `nivel`, `desde`, `hasta`, `activo` |
| `eventos_log` | Bitácora de mensajes entre actores | `mensaje`, `actor`, `texto`, `creado_en` |
| `config`, `seq` | Sal para los hashes y contadores de id | — |

**Por qué JSON:** es simple, no requiere instalar nada y es ideal para una demo. **Límite:** no escala a muchos usuarios simultáneos; en producción se reemplazaría por una base relacional (PostgreSQL/PostGIS) sin cambiar la API ni la vista, porque solo `app/db.py` y `app/models.py` tocan los datos.

## 9. API REST
| Método | Ruta | Quién | Acción |
|---|---|---|---|
| GET | `/api/estado` | Público (el personal ve más) | Estado del sistema |
| POST | `/api/login` · `/api/logout` | Público | Iniciar / cerrar sesión |
| POST | `/api/reportes` | Público | Crea un reclamo (registra IP y dispositivo; puede responder 409 si está bloqueado) |
| POST | `/api/recolector` | Público | Horario del recolector por dirección o zona |
| POST | `/api/contexto` | Operador | Cambia clima, turno o evento (recalcula el mapa) |
| POST | `/api/reportes/{id}/validar` · `/descartar` | Operador | Revisa un reclamo |
| POST | `/api/propuesta/decidir` | Operador, Admin | N1/N4: `{decision, zonas?, motivo?}` |
| POST | `/api/propuesta/escalar` · `/revisar` | Operador | Simula falta de respuesta · vuelve a revisar |
| POST | `/api/despachar` | Operador, Admin | N2: ordena la salida (solo con ruta aprobada) |
| POST | `/api/cuadrilla/salida` · `/resultado` | Operador | Mensajes 9 y 10, con verificación de reclamos |
| POST | `/api/turno/nuevo` | Operador | Cierra el turno y prepara otra propuesta |
| POST | `/api/recalibracion/decidir` · `/semana` | Admin | Mensajes 11–12 |
| GET | `/api/admin/resumen` | Admin, Desarrollador | Bloqueos, autores, usuarios |
| POST | `/api/admin/desbloquear/{id}` | Admin | Levanta un bloqueo |
| POST | `/api/demo/reset` | Desarrollador | Reinicia los datos de prueba |

Sin sesión → **401**; sin permiso → **403**; regla de negocio incumplida → **409** con un mensaje claro.

## 10. Cómo calcula el riesgo (explicable, sin caja negra)
```
puntaje = histórico(zona, turno) × (1 + factor_clima) + 0,20 si hay evento en la zona + 0,15 por cada reclamo validado
nivel   = alto (≥ 0,70) · medio (≥ 0,50) · bajo (< 0,50)
```
Factores de clima: normal 0, lluvia 0,15, calor 0,25. La ruta propuesta incluye zonas de nivel medio y alto, ordenadas por puntaje; **una zona de riesgo bajo no se recorre, pero un reclamo validado puede subirla a la ruta**.

**Sobre la IA (honestidad técnica):** hoy los agentes funcionan con **reglas simples y explicables, no con un modelo entrenado**. Está previsto sumar un modelo de lenguaje (API de Groq) para que el Agente 1 ajuste el puntaje dentro de un margen pequeño con una explicación, y el Agente 2 ordene la ruta con una justificación. **Plan B:** tiempo límite corto, validación de la respuesta, interruptor para apagar la IA, y la pantalla indicará siempre si la propuesta vino de la IA o de las reglas. La clave de la API va solo en un archivo `.env` (nunca en el navegador ni en GitHub). La decisión seguirá siendo de una persona.

## 11. Diseño del agente (PEAS)
- **Agente 1:** precisión ≥ 75 % semanal en zonas de riesgo alto con desborde real (si baja, se propone recalibrar); cobertura ≥ 70 % de desbordes en zonas marcadas. Sensores: datos abiertos (línea de base anual, supuesto), clima, calendario, reclamos. Actuador: mapa de riesgo.
- **Agente 2:** reducción ≥ 15 % de km sin recolección efectiva a los 2 meses, **sin que suban los desbordes** (meta del semestre: −45 %). Actuador: propuesta de ruta.
- **Operador:** tiempo entre alerta y respuesta asignada ≤ 24 h.
- **Entorno:** parcialmente observable, estocástico, secuencial, dinámico, discreto y multiagente cooperativo.

## 12. Caminos de falla contemplados
1. **Se corta una fuente de datos:** el Agente 1 no inventa; reutiliza el último mapa y baja la confianza.
2. **La persona no contesta:** recordatorio a las 2 h → escalada al Admin → si nadie responde, no se despacha nada (se prueba con «Simular: pasaron 2 horas»).
3. **Dos agentes se contradicen:** tras un intercambio, se escala y decide una persona.
4. **Reclamos abusivos:** bloqueo temporal por dispositivo/IP y revisión del Admin.

## 13. Instalación y uso
```bash
python server.py          # puerto 8000
python server.py 8080     # otro puerto
```
Abrir `http://localhost:8000`. Si Windows no reconoce `python`, usar `py server.py`. Para probar las reglas del backend: `python tests/smoke.py`.

## 14. Guía de prueba paso a paso
**Preparación.** 1) En la carpeta del proyecto: `python tests/smoke.py` → debe decir **OK**. 2) `python server.py` y abrir `http://localhost:8000` (recargar con **Ctrl + F5**). Se recomienda empezar con «Reiniciar demo» (ingresando como `dev`) para tener datos limpios.

**A. Usuario: reclamo.** Usuario → *Hacer un reclamo* → tipo «Desborde de basura», zona *Parque*, dirección «Libertador 500», texto → *Enviar*. Aparece «✔ Reclamo enviado» y el reclamo en *Últimos reclamos* como PENDIENTE.

**B. Usuario: horario del recolector.** *¿Cuándo pasa el recolector?* → «San Martín 1200» → zona *Centro*, horarios y si ya pasó o en cuánto tiempo. Probar «Calle inventada 5»: da error con calles de ejemplo; elegir una zona en la lista y repetir.

**C. Login.** Pantalla principal → *Personal*. Con contraseña incorrecta → error. Con `operador / operador123` → entra.

**D. Operador: validar y decidir.** *Operador de Higiene Urbana*. 1) En la sección 3, el reclamo del Parque está pendiente → *Validar*: aparece en «Ya revisados» y el puntaje de Parque sube. 2) Cambiar clima, turno o evento: el mapa y la ruta cambian. 3) *Ajustar*: tocar zonas en cierto orden (se numeran) → *Confirmar ajuste*: la ruta final respeta ese orden. 4) *Despachar* (estaba bloqueado hasta decidir).

**E. Cuadrilla: verificación en la calle.** Volver → *Cuadrilla* → *Confirmar salida*. Aparece una ficha por cada reclamo validado cuya zona está en la ruta. Probar los tres caminos: *¿Pasaste? Sí → ¿Había desborde? Sí → cantidad* = **RESUELTO**; *Sí → No* = **NO CONSTATADO**; *No → motivo* = vuelve a **PENDIENTE**. *Enviar resultado*. Verificar en el Operador (sección 5 y reclamos con su comentario) y en el Usuario (*Últimos reclamos*).

**F. Escalada (N4).** Como Operador: *Preparar un nuevo turno* y *Simular: pasaron 2 horas sin respuesta*. *Cerrar sesión* → entrar como `admin / admin123` → *Supervisión*: aparece la decisión pendiente → *Aprobar ruta* → *Ordenar salida de la cuadrilla*. Más abajo, *Aceptar recalibración* (mensaje 12). Comprobar que el Admin **no** puede decidir si no hubo escalada.

**G. Bloqueo por reclamos reiterados.** Como Usuario, desde la misma ventana, enviar **4 reclamos seguidos** (en menos de 10 minutos): los 3 primeros se aceptan y el **4.º se rechaza** con «Tu dispositivo quedó bloqueado hasta las HH:MM». Entrar como `admin` → *Usuarios y bloqueos*: aparece el bloqueo y el autor agrupado (IP parcial, sin la IP real) → *Desbloquear* → el Usuario puede reclamar de nuevo (si reincide, el bloqueo es de 1 h). En una **ventana de incógnito** (otro dispositivo) sí puede reclamar.

**H. Permisos.** Sin sesión, en la consola del navegador (F12): `fetch('/api/admin/resumen').then(r=>console.log(r.status))` → **401**. Como Operador, la misma línea → **403**.

**I. Desarrollador.** Entrar como `dev / dev123` → *Panel técnico*: resumen de datos y *Reiniciar demo*.

**J. Persistencia y privacidad.** Detener el servidor (Ctrl + C) y volver a iniciarlo: los datos siguen. Abrir `data/datos.json`: los reclamos guardan `ip_hash` y `dev_hash`, **no la IP real**.

### Guion de demo sugerido (≈ 3 min)
1. **Usuario:** hace un reclamo (queda guardado).
2. **Operador:** lo valida, cambia el clima (el mapa se recalcula), ve la alerta temprana y el botón «Despachar» bloqueado; ajusta el orden y despacha.
3. **Cuadrilla:** verifica el reclamo en la calle → resuelto.
4. **Admin:** muestra recalibración, escalada y bloqueos.
5. Mostrar la **bitácora numerada** (coincide con el diagrama de secuencia).

## 15. Estructura del proyecto
```
mendoza_limpia/
├── server.py            # servidor HTTP, sesión e identificación IP/dispositivo
├── data/
│   ├── datos_mock.json  # datos de prueba iniciales
│   └── datos.json       # datos vivos (se crea solo)
├── app/
│   ├── db.py            # JSON, usuarios de demo y migración
│   ├── auth.py          # login y sesiones
│   ├── security.py      # IP/dispositivo hasheados y bloqueos
│   ├── models.py        # reglas de negocio (N1–N4, ciclo del reclamo)
│   ├── predictor.py     # Agentes 1 y 2 (reglas explicables)
│   ├── recorridos.py    # horarios del recolector (datos de prueba)
│   └── controllers.py   # endpoints y permisos por rol
├── static/              # vista: index.html, app.js, style.css
├── tests/smoke.py       # prueba de reglas del backend
└── .gitignore           # excluye datos vivos y .env
```

## 16. Alcance, supuestos y límites (honestidad técnica)
- **Todo dato es de prueba.** No usa sensores reales ni datos abiertos en vivo; los horarios y calles del recolector son de ejemplo.
- Los reclamos hoy son telefónicos o presenciales: el **formulario digital** es un supuesto a desarrollar.
- **No reemplaza al Operador** ni promete detectar el 100 % de los desbordes: anticipa los de alta probabilidad.
- **Autenticación de demo:** usuarios y contraseñas escritos en el código, sesiones en memoria y sin límite de intentos de login. Suficiente para una presentación, no para producción.
- **IP y dispositivo:** pueden evadirse con incógnito o borrando datos del navegador; una IP compartida podría afectar a otras personas (por eso se prioriza el dispositivo).
- Los valores de precisión (72 %), cobertura (68 %) y km (−12 %) del Admin son ilustrativos.

## 17. Hoja de ruta
Integración con Groq con plan B · modelo de riesgo entrenado y calibrado · autenticación robusta · formulario con foto y geolocalización · mapa interactivo · conexión a datos abiertos y API meteorológica · optimización real de rutas · sensores IoT opcionales · tablero de métricas (precisión, cobertura, km, tiempo de respuesta) · base relacional · expansión a otros municipios del Gran Mendoza.

## 18. Modelo de negocio (canvas)
**Clientes:** Área de Higiene Urbana de la Municipalidad de Mendoza (primeros usuarios: Dirección de Higiene Urbana y su programa GIRSU). **Canales:** integración con el área, portal de datos abiertos, vínculo con cooperativas de recuperadores urbanos. **Ingresos:** convenio con la Municipalidad, licenciamiento a otros municipios, ahorro operativo. **Costos:** desarrollo y mantenimiento del modelo, procesamiento de datos, capacitación del personal, sensores IoT (opcional).

## 19. Uso de IA
Se usó Claude (Anthropic) como apoyo para el diseño, el código y la documentación. El equipo revisó y adaptó el contenido.
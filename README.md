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
Dos agentes de software y personas que conservan la decisión final:

| Agente / actor | Tipo | Qué hace |
|---|---|---|
| **Agente 1 — Predictor de Acumulación** | Software | Calcula cada día el riesgo por zona y turno (alto/medio/bajo) con datos históricos, clima, eventos y reportes validados. |
| **Agente 2 — Planificador de Rutas** | Software | Propone ruta y frecuencia por turno, con las zonas de riesgo alto primero. No asigna camiones. |
| **Operador de Higiene Urbana** | Persona | Valida reportes, aprueba/ajusta/rechaza la ruta y despacha la cuadrilla. |
| **Supervisor** | Persona | Decide la recalibración semanal del modelo y resuelve cuando el Operador no responde. |
| **Cuadrilla de recolección** | Persona | Confirma la salida, recorre la ruta e informa el resultado real. |
| **Vecino / inspector** | Persona | Informa desbordes. Su reporte es un dato que el Operador valida antes de usarse. |

**Propuesta de valor:** reducir kilómetros recorridos sin recolección efectiva (hipótesis: −45 % en el primer semestre) usando datos públicos de la Ciudad combinados con clima y calendario, sin depender de sensores costosos.

## 3. Reglas no delegables (se cumplen también en el backend)
| Marca | Decisión humana | Cómo lo hace cumplir el sistema |
|---|---|---|
| **N1** | Aprobar, ajustar o rechazar la ruta | `models.decidir` solo acepta actores humanos; ningún agente decide. |
| **N2** | Despachar a la cuadrilla | `models.despachar` rechaza (HTTP 409) si no hay una ruta aprobada por una persona. |
| **N3** | Resolver contradicciones entre agentes | La propuesta llega marcada al Operador; ningún agente impone su versión. |
| **N4** | Decidir cuando el Operador no responde | El Supervisor solo puede decidir si hubo escalada; si nadie responde, **no se despacha nada**. |

El silencio nunca cuenta como permiso. La decisión no delegable del canvas es la **reasignación de personal / despacho de la cuadrilla**; las multas quedan fuera del alcance del sistema.

## 4. Arquitectura MVC
```
 Navegador (Vista)  ──HTTP/JSON──▶  server.py (enrutador)
 static/index.html                       │
 static/app.js, style.css                ▼
                                  app/controllers.py   (Controlador)
                                         │
                                         ▼
                      app/models.py + app/predictor.py   (Modelo + agentes)
                                         │
                                         ▼
                              app/db.py ── archivo JSON (data/datos.json)
```
- **Modelo (`app/models.py`, `app/predictor.py`, `app/db.py`, `data/`):** reglas de negocio, acceso a datos y los dos agentes. Aquí se hacen cumplir N1–N4.
- **Vista (`static/`):** interfaz web con un ingreso por rol. Se actualiza sola cada 2,5 s: lo que carga el vecino aparece en el panel del Operador.
- **Controlador (`app/controllers.py`):** traduce cada endpoint a una operación del modelo y devuelve el estado completo.
- **Sin dependencias externas:** solo la biblioteca estándar de Python 3.8+ (`http.server`, `json`).

## 5. Almacenamiento de datos (archivo JSON)
Los datos se guardan en **`data/datos.json`**, un archivo de texto que se puede abrir y leer. Se crea solo la primera vez, copiando los **datos de prueba (mock)** de `data/datos_mock.json`. Cada cambio se escribe de forma atómica (archivo temporal + reemplazo) y con bloqueo, para que dos pestañas no se pisen. El botón **«Reiniciar demo»** restaura los datos de prueba.

| Colección | Para qué sirve | Campos principales |
|---|---|---|
| `zonas` | Catálogo de zonas con su histórico | `nombre`, `hist_manana`, `hist_tarde`, `afectada_evento` |
| `contexto` | Datos del día | `clima`, `turno`, `evento` |
| `reportes` | Reclamos de vecinos/inspectores (mensaje 0) | `zona_id`, `descripcion`, `origen`, `estado` (pendiente/validado/descartado), `usado`, `creado_en`, `validado_en` |
| `propuestas` | Ruta propuesta y decisión humana (N1) | `ruta`, `estado`, `ruta_final`, `motivo`, `decidido_por`, `escalada`, fechas |
| `despachos` | Salida de la cuadrilla y resultado (N2, mensajes 8–10) | `propuesta_id`, `ordenado_por`, `salida_confirmada_en`, `contenedores`, `desbordes`, `resultado_en` |
| `recalibraciones` | Control semanal del modelo (mensajes 11–12) | `precision`, `cobertura`, `km_var`, `estado`, `decidido_por` |
| `eventos_log` | Bitácora de mensajes entre actores (trazabilidad) | `mensaje`, `actor`, `texto`, `creado_en` |
| `seq` | Contadores de identificadores | uno por colección |

**Relaciones:** `reportes.zona_id → zonas.id`; `despachos.propuesta_id → propuestas.id`. Se guarda quién decidió cada cosa y cuándo, para poder auditar y medir el tiempo de respuesta (meta ≤ 24 h).

**Por qué JSON:** es simple, no requiere instalar nada y es ideal para una demo de hackatón. **Límite:** no escala a muchos usuarios simultáneos; en producción se reemplazaría por una base relacional (PostgreSQL/PostGIS) sin cambiar la API ni la vista, porque solo `app/db.py` y `app/models.py` tocan los datos.

## 6. API REST
| Método | Ruta | Acción |
|---|---|---|
| GET | `/api/estado` | Estado completo (mapa, propuesta, reportes, bitácora) |
| POST | `/api/contexto` | Cambia clima, turno o evento (recalcula el mapa) |
| POST | `/api/reportes` | Crea un reporte `{zona, descripcion, origen}` |
| POST | `/api/reportes/{id}/validar` · `/descartar` | El Operador revisa un reporte |
| POST | `/api/propuesta/decidir` | N1/N4: `{decision, actor, zonas?, motivo?}` |
| POST | `/api/propuesta/escalar` · `/revisar` | Simula falta de respuesta · vuelve a revisar |
| POST | `/api/despachar` | N2: ordena la salida (solo con ruta aprobada) |
| POST | `/api/cuadrilla/salida` · `/resultado` | Mensajes 9 y 10 |
| POST | `/api/turno/nuevo` | Cierra el turno y prepara otra propuesta |
| POST | `/api/recalibracion/decidir` · `/semana` | Mensajes 11–12 |
| POST | `/api/demo/reset` | Reinicia la base con datos de prueba |

Los errores de reglas de negocio responden **HTTP 409** con un mensaje claro.

## 7. Cómo calcula el riesgo (explicable, sin caja negra)
```
puntaje = histórico(zona, turno) × (1 + factor_clima) + 0,20 si hay evento en la zona + 0,15 por cada reporte validado
nivel   = alto (≥ 0,70) · medio (≥ 0,50) · bajo (< 0,50)
```
Factores de clima: normal 0, lluvia 0,15, calor 0,25. La ruta propuesta incluye zonas de nivel medio y alto, ordenadas por puntaje. Son **reglas simples, no un modelo entrenado**; en una versión real se reemplazarían por un modelo calibrado con datos históricos.

## 8. Diseño del agente (PEAS)
- **Agente 1:** precisión ≥ 75 % semanal en zonas de riesgo alto con desborde real (si baja, se propone recalibrar); cobertura ≥ 70 % de desbordes en zonas marcadas. Sensores: datos abiertos (línea de base anual, supuesto), clima, calendario de eventos, reportes. Actuador: mapa de riesgo.
- **Agente 2:** reducción ≥ 15 % de km sin recolección efectiva a los 2 meses, **sin que suban los desbordes** (meta del semestre: −45 %). Actuador: propuesta de ruta.
- **Operador:** tiempo entre alerta y respuesta asignada ≤ 24 h.
- **Entorno:** parcialmente observable (no hay sensores de llenado), estocástico, secuencial, dinámico, discreto y multiagente cooperativo.

## 9. Caminos de falla contemplados
1. **Se corta una fuente de datos:** el Agente 1 no inventa; reutiliza el último mapa y baja la confianza.
2. **La persona no contesta:** recordatorio a las 2 h → escalada al Supervisor → si nadie responde, no se despacha nada (probalo con «Simular: pasaron 2 horas»).
3. **Dos agentes se contradicen:** tras un intercambio, se escala y decide una persona.

## 10. Instalación y uso
```bash
python server.py          # puerto 8000
python server.py 8080     # otro puerto
```
Abrir `http://localhost:8000`. El archivo `data/datos.json` se crea solo con datos de prueba. Para probar las reglas: `python tests/smoke.py`.

### Guion de demo sugerido (≈ 3 min)
1. **Vecino:** enviar un reporte (queda guardado en el JSON).
2. **Operador:** ver el reporte pendiente, cambiar clima/evento (el mapa se recalcula), validarlo, ver la alerta temprana y el botón «Despachar» bloqueado.
3. Aprobar → despachar. Probar también **Ajustar** y **Rechazar**.
4. **Cuadrilla:** confirmar salida e informar el resultado → vuelve al Operador.
5. **Supervisor:** aceptar la recalibración; probar la escalada.
6. Mostrar la **bitácora numerada** (coincide con el diagrama de secuencia).

## 11. Estructura del proyecto
```
mendoza_limpia/
├── server.py            # servidor HTTP y enrutador
├── data/
│   ├── datos_mock.json  # datos de prueba iniciales
│   └── datos.json       # datos vivos (se crea solo)
├── app/
│   ├── db.py            # lectura/escritura del JSON
│   ├── models.py        # reglas de negocio (N1–N4)
│   ├── predictor.py     # Agentes 1 y 2 (reglas explicables)
│   └── controllers.py   # endpoints
├── static/              # vista: index.html, app.js, style.css
└── tests/smoke.py       # prueba de reglas del backend
```

## 12. Alcance, supuestos y límites (honestidad técnica)
- **Todo dato es de prueba.** No usa sensores reales ni datos abiertos en vivo; los datos abiertos de la Ciudad serían una línea de base anual (supuesto).
- El **formulario digital de reportes** es un supuesto a desarrollar: hoy el reporte es telefónico o presencial.
- **No reemplaza al Operador** ni promete detectar el 100 % de los desbordes: anticipa los de alta probabilidad.
- El ingreso por rol es una **simulación de demo, sin autenticación**.
- Los valores de precisión (72 %), cobertura (68 %) y km (−12 %) del Supervisor son ilustrativos.

## 13. Hoja de ruta
Autenticación con roles reales · conexión a datos abiertos y API meteorológica · formulario ciudadano con foto y geolocalización · mapa interactivo · optimización real de rutas · modelo entrenado y calibrado · sensores IoT opcionales · tablero de métricas (precisión, cobertura, km, tiempo de respuesta) · expansión a otros municipios del Gran Mendoza.

## 14. Modelo de negocio (canvas)
**Clientes:** Área de Higiene Urbana de la Municipalidad de Mendoza (primeros usuarios: Dirección de Higiene Urbana y su programa GIRSU). **Canales:** integración con el área, portal de datos abiertos, vínculo con cooperativas de recuperadores urbanos. **Ingresos:** convenio con la Municipalidad, licenciamiento a otros municipios, ahorro operativo. **Costos:** desarrollo y mantenimiento del modelo, procesamiento de datos, capacitación del personal, sensores IoT (opcional).

## 15. Uso de IA
Se usó Claude (Anthropic) como apoyo para el diseño, el código y la documentación. El equipo revisó y adaptó el contenido.

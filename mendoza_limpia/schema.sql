-- Mendoza Limpia · esquema de base de datos (SQLite)
CREATE TABLE IF NOT EXISTS zonas(
  id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL,
  hist_manana REAL NOT NULL, hist_tarde REAL NOT NULL, afectada_evento INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS contexto(            -- una sola fila: datos del día
  id INTEGER PRIMARY KEY CHECK(id=1), clima TEXT NOT NULL DEFAULT 'calor',
  turno INTEGER NOT NULL DEFAULT 0, evento INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS reportes(            -- mensaje 0: vecino/inspector -> Operador
  id INTEGER PRIMARY KEY, zona_id INTEGER NOT NULL REFERENCES zonas(id),
  descripcion TEXT NOT NULL, origen TEXT NOT NULL CHECK(origen IN('vecino','inspector')),
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK(estado IN('pendiente','validado','descartado')),
  usado INTEGER NOT NULL DEFAULT 0, creado_en TEXT NOT NULL, validado_en TEXT);
CREATE TABLE IF NOT EXISTS propuestas(          -- Agente 2 propone, una persona decide (N1)
  id INTEGER PRIMARY KEY, turno INTEGER NOT NULL, clima TEXT NOT NULL, evento INTEGER NOT NULL,
  ruta_json TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'pendiente'
    CHECK(estado IN('pendiente','aprobada','ajustada','rechazada','despachada','cerrada')),
  ruta_final_json TEXT, motivo TEXT, decidido_por TEXT, escalada INTEGER NOT NULL DEFAULT 0,
  creado_en TEXT NOT NULL, decidido_en TEXT);
CREATE TABLE IF NOT EXISTS despachos(           -- N2: salida de la cuadrilla (irreversible)
  id INTEGER PRIMARY KEY, propuesta_id INTEGER NOT NULL REFERENCES propuestas(id),
  ordenado_por TEXT NOT NULL, ordenado_en TEXT NOT NULL, salida_confirmada_en TEXT,
  contenedores INTEGER, desbordes INTEGER, resultado_en TEXT);
CREATE TABLE IF NOT EXISTS recalibraciones(     -- mensajes 11 y 12: control semanal del modelo
  id INTEGER PRIMARY KEY, precision REAL NOT NULL, cobertura REAL NOT NULL, km_var REAL NOT NULL,
  estado TEXT NOT NULL DEFAULT 'propuesta' CHECK(estado IN('propuesta','aceptada','rechazada')),
  decidido_por TEXT, creado_en TEXT NOT NULL, decidido_en TEXT);
CREATE TABLE IF NOT EXISTS eventos_log(         -- bitácora de mensajes entre actores
  id INTEGER PRIMARY KEY, mensaje TEXT, actor TEXT NOT NULL, texto TEXT NOT NULL, creado_en TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_rep_estado ON reportes(estado, creado_en);

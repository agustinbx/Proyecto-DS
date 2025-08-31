-- Tablas simples para series de tiempo de precios, market cap y volumen
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id TEXT NOT NULL,
    ts_ms INTEGER NOT NULL,       -- timestamp en milisegundos (UTC)
    price REAL,
    market_cap REAL,
    total_volume REAL,
    UNIQUE (coin_id, ts_ms)       -- evita duplicados
);

-- Vista de apoyo: agrega por día (UTC)
CREATE VIEW IF NOT EXISTS daily_agg AS
SELECT
   coin_id,
   date(ts_ms/1000, 'unixepoch') AS day_utc,
   AVG(price) AS avg_price,
   MIN(price) AS min_price,
   MAX(price) AS max_price,
   AVG(market_cap) AS avg_market_cap,
   AVG(total_volume) AS avg_total_volume
FROM price_history
GROUP BY coin_id, day_utc;
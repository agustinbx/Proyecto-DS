
import sqlite3
import time
import pandas as pd
import requests
import random

from .config import BASE_URL, HEADERS, COINS, VS_CURRENCY, DAYS, SQLITE_PATH

def _get_conn():
    return sqlite3.connect(SQLITE_PATH)

def init_db():
    with _get_conn() as conn, conn:
        with open("db/init.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        conn.executescript(sql)
    print("✔ DB inicializada")

def fetch_market_chart(coin_id: str, vs_currency: str, days: str = "30") -> dict:
    """
    Llama /coins/{id}/market_chart con backoff exponencial + jitter,
    respeta Retry-After en 429 y loggea cuerpo en 400 para diagnosticar.
    """
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}

    max_attempts = 8  # subimos margen de reintentos
    base_sleep = 2.0

    for attempt in range(max_attempts):
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        status = r.status_code

        if status == 200:
            return r.json()

        # Log útil para 400 (ver por qué)
        if status == 400:
            try:
                print(f"[{coin_id}] 400 body:", r.json())
            except Exception:
                print(f"[{coin_id}] 400 text:", r.text)

        # Si 429 (rate limit): respetar Retry-After
        if status == 429:
            retry_after = r.headers.get("Retry-After")
            if retry_after:
                try:
                    wait_s = float(retry_after)
                except ValueError:
                    wait_s = base_sleep * (2 ** attempt)
            else:
                wait_s = base_sleep * (2 ** attempt)
        else:
            # Otros errores: backoff exponencial con jitter
            wait_s = base_sleep * (2 ** attempt)

        # Jitter aleatorio (±30%) para evitar sincronía con otros clientes
        jitter = random.uniform(0.7, 1.3)
        wait_s = wait_s * jitter
        wait_s = min(wait_s, 60.0)  # cap de seguridad

        print(f"[{coin_id}] Error {status}. Reintentando en {wait_s:.1f}s...")
        time.sleep(wait_s)

    r.raise_for_status()

def normalize_market_chart(coin_id: str, payload: dict) -> pd.DataFrame:
    """
    payload={'prices': [[ts_ms, value],...], 'market_caps': [...], 'total_volumes': [...]}
    """
    def pairs_to_df(pairs, colname):
        return pd.DataFrame(pairs, columns=["ts_ms", colname]).dropna()

    p = pairs_to_df(payload.get("prices", []), "price")
    m = pairs_to_df(payload.get("market_caps", []), "market_cap")
    v = pairs_to_df(payload.get("total_volumes", []), "total_volume")

    # Merge por timestamp
    df = p.merge(m, on="ts_ms", how="outer").merge(v, on="ts_ms", how="outer")
    df["coin_id"] = coin_id

    # Orden y tipos
    df = df[["coin_id", "ts_ms", "price", "market_cap", "total_volume"]]
    df = df.dropna(subset=["ts_ms"])
    df["ts_ms"] = df["ts_ms"].astype("int64")
    return df

def upsert_df(df: pd.DataFrame):
    # Estrategia: tabla temporal + INSERT OR IGNORE para respetar UNIQUE (coin_id, ts_ms)
    with _get_conn() as conn, conn:
        df.to_sql("price_history_temp", conn, if_exists="replace", index=False)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO price_history (coin_id, ts_ms, price, market_cap, total_volume)
            SELECT coin_id, ts_ms, price, market_cap, total_volume
            FROM price_history_temp;
        """)
        inserted = conn.total_changes
        cur.execute("DROP TABLE IF EXISTS price_history_temp;")
    return inserted

def run_etl():
    from .config import BASE_URL, COINS, VS_CURRENCY, DAYS
    print(f"→ BASE_URL: {BASE_URL}")
    print(f"→ COINS: {COINS} | VS: {VS_CURRENCY} | DAYS: {DAYS}")
    init_db()
    total_rows = 0
    for coin in COINS:
        print(f"→ Descargando {coin} ({DAYS} días, vs={VS_CURRENCY})")
        data = fetch_market_chart(coin, VS_CURRENCY, DAYS)
        df = normalize_market_chart(coin, data)
        inserted = upsert_df(df)
        print(f"   ✔ Insertadas/ignoradas: {inserted} filas")
        total_rows += inserted

        # --- pausa entre monedas para no gatillar rate limit ---
        time.sleep(3)

    print(f"✔ ETL finalizada. Filas afectadas: {total_rows}")
    return total_rows
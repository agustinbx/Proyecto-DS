
import sqlite3
import time
import pandas as pd
import requests

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
    Usa /coins/{id}/market_chart para traer series de: prices, market_caps, total_volumes
    https://www.coingecko.com/en/api/documentation
    """
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    for attempt in range(5):
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        # Backoff simple
        sleep_s = 2 ** attempt
        print(f"[{coin_id}] Error {r.status_code}. Reintentando en {sleep_s}s...")
        time.sleep(sleep_s)
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
    init_db()
    total_rows = 0
    for coin in COINS:
        print(f"→ Descargando {coin} ({DAYS} días, vs={VS_CURRENCY})")
        data = fetch_market_chart(coin, VS_CURRENCY, DAYS)
        df = normalize_market_chart(coin, data)
        inserted = upsert_df(df)
        print(f"   ✔ Insertadas/ignoradas: {inserted} filas")
        total_rows += inserted
    print(f"✔ ETL finalizada. Filas afectadas: {total_rows}")
    return total_rows

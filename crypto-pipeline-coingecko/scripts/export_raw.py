import os
import sqlite3
import pandas as pd

DB_PATH = os.getenv("SQLITE_PATH", "./crypto.db")
COIN = "bitcoin"   # podés cambiarlo por ethereum, solana, etc.

OUT_DIR = "./data"
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    query = """
    SELECT
        coin_id,
        datetime(ts_ms/1000, 'unixepoch') AS ts_utc,
        price,
        market_cap,
        total_volume
    FROM price_history
    WHERE coin_id = ?
    ORDER BY ts_ms
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=(COIN,))

    # Exportar tal cual
    json_path = os.path.join(OUT_DIR, f"{COIN}_raw.json")
    csv_path  = os.path.join(OUT_DIR, f"{COIN}_raw.csv")

    df.to_json(json_path, orient="records", date_format="iso", force_ascii=False)
    df.to_csv(csv_path, index=False)

    print(f"✔ Exportado JSON: {json_path} ({len(df)} filas)")
    print(f"✔ Exportado CSV : {csv_path}")

if __name__ == "__main__":
    main()
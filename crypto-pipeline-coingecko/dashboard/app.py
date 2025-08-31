import sqlite3
import pandas as pd
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

@st.cache_data(ttl=300)
def load_coins(conn_path):
    with sqlite3.connect(conn_path) as conn:
        coins = pd.read_sql_query("SELECT DISTINCT coin_id FROM price_history ORDER BY coin_id", conn)
    return coins["coin_id"].tolist()

@st.cache_data(ttl=300)
def load_time_series(conn_path, coin, start_day, end_day):
    query = """
    SELECT
        coin_id,
        datetime(ts_ms/1000, 'unixepoch') AS ts,
        price,
        market_cap,
        total_volume
    FROM price_history
    WHERE coin_id = ?
      AND date(ts_ms/1000, 'unixepoch') BETWEEN ? AND ?
    ORDER BY ts_ms
    """
    with sqlite3.connect(conn_path) as conn:
        df = pd.read_sql_query(query, conn, params=(coin, start_day, end_day))
    return df

def main():
    st.title("📈 Crypto Dashboard — CoinGecko")
    conn_path = st.text_input("Ruta SQLite", "./crypto.db")
    if not conn_path:
        st.stop()

    coins = load_coins(conn_path)
    if not coins:
        st.info("No hay datos aún. Corré el ETL para poblar la base.")
        st.stop()

    coin = st.selectbox("Moneda", coins, index=0)
    col1, col2 = st.columns(2)
    with col1:
        start_day = st.date_input("Desde", date.today() - timedelta(days=30))
    with col2:
        end_day = st.date_input("Hasta", date.today())

    if start_day > end_day:
        st.error("El rango de fechas es inválido.")
        st.stop()

    df = load_time_series(conn_path, coin, str(start_day), str(end_day))
    if df.empty:
        st.warning("No hay datos para ese rango.")
        st.stop()

    st.subheader(f"Serie de {coin.upper()}")
    st.line_chart(df.set_index("ts")["price"], height=300)
    st.caption("Precio (vs_currency configurada en ETL)")

    with st.expander("Detalles y últimas filas"):
        st.dataframe(df.tail(20), use_container_width=True)

    # KPIs simples
    last_price = df["price"].iloc[-1]
    first_price = df["price"].iloc[0]
    ret = (last_price/first_price - 1) * 100 if first_price else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Precio actual", f"{last_price:,.2f}")
    c2.metric("Variación periodo", f"{ret:,.2f}%")
    c3.metric("Observaciones", len(df))

if __name__ == "__main__":
    main()

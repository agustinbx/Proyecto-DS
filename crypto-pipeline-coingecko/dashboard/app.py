import sqlite3
import pandas as pd
import streamlit as st
from datetime import date, timedelta

#Streamlit es una librería que transforma un script de Python en una aplicación web interactiva.
#No trae dashboards “prediseñados” como tal.
#Lo que hacés es usar funciones de Streamlit (st.title, st.line_chart, st.dataframe, etc.) para armar tu propia interfaz.

# dashboard/app.py
import os
import re
import json
import time
import sqlite3
import requests
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from dotenv import load_dotenv

# ---------- Config ----------
st.set_page_config(page_title="BTC Dashboard", layout="wide")
load_dotenv()

COIN = "bitcoin"
SQLITE_PATH = os.getenv("SQLITE_PATH", "./crypto.db").strip()
VS_CURRENCY = os.getenv("VS_CURRENCY", "usd").strip()
API_KEY = (os.getenv("COINGECKO_API_KEY") or "").strip()

# Inferir endpoint según key (demo/public vs pro)
if not API_KEY or API_KEY.lower().startswith("demo_"):
    BASE_URL = "https://api.coingecko.com/api/v3"
    HEADERS = {}
else:
    BASE_URL = "https://pro-api.coingecko.com/api/v3"
    HEADERS = {"x-cg-pro-api-key": API_KEY}

# ---------- Helpers ----------
def strip_html(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<.*?>", "", s)
    return s.strip()

@st.cache_data(ttl=300)
def load_time_series(conn_path, start_day, end_day):
    query = """
    SELECT
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
        df = pd.read_sql_query(query, conn, params=(COIN, str(start_day), str(end_day)))
    return df

@st.cache_data(ttl=300)
def fetch_btc_metadata():
    """Trae /coins/bitcoin con market_data + comunidad + dev, sin tickers."""
    url = f"{BASE_URL}/coins/{COIN}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "true",
        "developer_data": "true",
        "sparkline": "false",
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def kfmt(x):
    try:
        x = float(x)
    except Exception:
        return "-"
    # formato compacto: 1.2K, 3.4M, 5.6B
    absx = abs(x)
    if absx >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}B"
    if absx >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if absx >= 1_000:
        return f"{x/1_000:.2f}K"
    return f"{x:,.2f}"

# ---------- UI ----------
st.title("₿ BTC — Dashboard (CoinGecko + SQLite)")

# Rango de fechas para la serie histórica
colA, colB = st.columns(2)
with colA:
    start_day = st.date_input("Desde", date.today() - timedelta(days=30))
with colB:
    end_day = st.date_input("Hasta", date.today())

if start_day > end_day:
    st.error("El rango de fechas es inválido.")
    st.stop()

# Cargar serie de precios desde SQLite
df = load_time_series(SQLITE_PATH, start_day, end_day)
if df.empty:
    st.info("No hay datos en la base para BTC y ese rango. Corré el ETL primero.")
    st.stop()

# Traer metadata en vivo
try:
    meta = fetch_btc_metadata()
except requests.HTTPError as e:
    st.warning(f"No pude traer metadata en vivo ({e}). Muestro solo la serie histórica.")
    meta = {}

# Header con logo + nombre/símbolo
logo = meta.get("image", {}).get("small") or meta.get("image", {}).get("thumb")
name = meta.get("name", "Bitcoin")
symbol = meta.get("symbol", "btc").upper()

col1, col2 = st.columns([1, 5])
with col1:
    if logo:
        st.image(logo, width=64)
with col2:
    st.subheader(f"{name} ({symbol})")

# KPIs a partir de market_data
md = meta.get("market_data", {}) if meta else {}
current = md.get("current_price", {}).get(VS_CURRENCY)
chg24 = md.get("price_change_percentage_24h")
mcap = md.get("market_cap", {}).get(VS_CURRENCY)
vol24 = md.get("total_volume", {}).get(VS_CURRENCY)
ath = md.get("ath", {}).get(VS_CURRENCY)
atl = md.get("atl", {}).get(VS_CURRENCY)
ath_date = md.get("ath_date", {}).get(VS_CURRENCY) or "-"
atl_date = md.get("atl_date", {}).get(VS_CURRENCY) or "-"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Precio actual", f"{current:,.2f}" if current else "-", f"{chg24:.2f}%" if chg24 is not None else None)
c2.metric("Market Cap", kfmt(mcap))
c3.metric("Volumen 24h", kfmt(vol24))
c4.metric("ATH / ATL", f"{ath:,.2f} / {atl:,.2f}" if (ath and atl) else "-")

st.caption(f"ATH fecha: {ath_date}  |  ATL fecha: {atl_date}")

# Descripción corta (en inglés, se puede adaptar a otro idioma si querés)
desc = (meta.get("description", {}) or {}).get("en", "")
desc = strip_html(desc)
if desc:
    with st.expander("Descripción del proyecto"):
        st.write(desc[:800] + ("..." if len(desc) > 800 else ""))

# Gráfico de precio del rango seleccionado (de la DB)
st.subheader("Precio (serie histórica en DB)")
st.line_chart(df.set_index("ts")["price"], height=320)
st.caption(f"Fuente: SQLite ({SQLITE_PATH}) — vs_currency={VS_CURRENCY}")

# Tabla de últimas filas
with st.expander("Últimas filas"):
    st.dataframe(df.tail(25), use_container_width=True)


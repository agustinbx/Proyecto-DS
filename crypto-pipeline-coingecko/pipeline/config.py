import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Lee la API key (puede estar vacía si usás la API pública sin plan pro)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "").strip()

# Lista de monedas (separadas por coma en el .env)
COINS = [c.strip() for c in os.getenv("COINS", "bitcoin,ethereum").split(",") if c.strip()]

# Moneda fiat (usd, eur, ars, etc.)
VS_CURRENCY = os.getenv("VS_CURRENCY", "usd").strip()

# Cantidad de días de histórico a descargar
DAYS = os.getenv("DAYS", "31").strip()

# Ruta a la base de datos SQLite
SQLITE_PATH = os.getenv("SQLITE_PATH", "./crypto.db").strip()


# Permite forzar el dominio por .env si querés (opcional)
ENV_BASE = os.getenv("COINGECKO_BASE_URL", "").strip()

def _infer_base_url(api_key: str) -> str:
    """
    - Sin key o demo -> api.coingecko.com
    - Con key Pro real -> pro-api.coingecko.com
    """
    if not api_key:
        return "https://api.coingecko.com/api/v3"
    # algunas claves demo vienen con 'demo' en el valor o no habilitan pro
    if "demo" in api_key.lower():
        return "https://api.coingecko.com/api/v3"
    # por defecto, si hay key asumimos Pro
    return "https://pro-api.coingecko.com/api/v3"

BASE_URL = ENV_BASE or _infer_base_url(COINGECKO_API_KEY)

HEADERS = {}
# Solo enviar header si hay key y estamos en dominio pro
if COINGECKO_API_KEY and "pro-api.coingecko.com" in BASE_URL:
    HEADERS["x-cg-pro-api-key"] = COINGECKO_API_KEY
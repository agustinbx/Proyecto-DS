import requests
import json

BASE_URL = "https://api.coingecko.com/api/v3"

def get_coin_metadata(coin_id="bitcoin"):
    url = f"{BASE_URL}/coins/{coin_id}"
    params = {
        "localization": "false",   # desactiva traducciones
        "tickers": "false",        # no bajar todos los pares (más liviano)
        "market_data": "true",     # incluir precios, market cap, volumen
        "community_data": "true",  # incluir datos sociales
        "developer_data": "true",  # incluir datos dev
        "sparkline": "false"
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    data = get_coin_metadata("bitcoin")
    # guardar como json
    with open("data/bitcoin_metadata.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✔ Metadata exportada a data/bitcoin_metadata.json")

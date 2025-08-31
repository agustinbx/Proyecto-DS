# 📈 Crypto Data Pipeline — CoinGecko + SQLite + Streamlit

Proyecto práctico de **Ciencia de Datos / Ingeniería de Datos** que implementa un pipeline de criptomonedas usando la API de [CoinGecko](https://www.coingecko.com/), almacenamiento en SQLite, análisis exploratorio y visualización interactiva con Streamlit.

---

## 🚀 Objetivos del proyecto
- Extraer datos de precios de criptomonedas desde una API pública.
- Procesar y guardar los datos en una base SQLite con control de duplicados.
- Realizar un análisis exploratorio de series temporales (EDA).
- Construir un **dashboard interactivo** para visualizar precios, retornos y métricas básicas.
- Sentar las bases para modelos sencillos de predicción (ej: regresión logística para “día sube/baja”).

---

## 🛠️ Tecnologías utilizadas
- **Python 3.10+**
- [requests](https://pypi.org/project/requests/) → llamadas a la API.
- [pandas](https://pandas.pydata.org/) → transformación y análisis de datos.
- [sqlite3](https://docs.python.org/3/library/sqlite3.html) → almacenamiento.
- [streamlit](https://streamlit.io/) → dashboard web interactivo.
- [schedule](https://pypi.org/project/schedule/) → automatización de tareas.

---

## 📂 Estructura del proyecto
#!/usr/bin/env python3
"""
Descarga velas (klines) históricas de BTC/USDT Futures (USDT-M) desde
Binance Vision (data.binance.vision) y las une en un único CSV.

Uso:
    python3 download_btcusdt_klines.py

Requisitos:
    pip3 install requests pandas

Configura abajo el símbolo, el intervalo y los meses que quieras descargar.
"""

import os
import zipfile
import io
from typing import Optional
import requests
import pandas as pd

# ----------------------- CONFIGURACIÓN -----------------------

SYMBOL = "BTCUSDT"
INTERVAL = "15m"          # 15 minutos
MARKET = "um"             # um = USDT-M futures (BTCUSDT perpetuo)

# Lista de meses a descargar en formato (año, mes). Edita esto a tu gusto.
MONTHS = [
   (2024, 5), (2024, 6), (2024, 7), (2024, 8),
   (2024, 9), (2024, 10), (2024, 11), (2024, 12),
   (2025, 5), (2025, 6), (2025, 7), (2025, 8),
   (2025, 9), (2025, 10), (2025, 11), (2025, 12),
   (2026, 1), (2026, 2), (2026, 3), (2026, 4),
  ]

OUTPUT_DIR = "btcusdt_klines_data"
FINAL_CSV = f"{SYMBOL}_{INTERVAL}_combined.csv"

COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
]

BASE_URL = f"https://data.binance.vision/data/futures/{MARKET}/monthly/klines/{SYMBOL}/{INTERVAL}"

# ----------------------- DESCARGA -----------------------

def download_month(year: int, month: int) -> Optional[pd.DataFrame]:
    filename = f"{SYMBOL}-{INTERVAL}-{year}-{month:02d}.zip"
    url = f"{BASE_URL}/{filename}"
    print(f"Descargando {filename} ...")

    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        print(f"  -> No disponible ({resp.status_code}): {url}")
        return None

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f, header=None, names=COLUMNS)

    print(f"  -> OK, {len(df)} velas")
    return df


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_dfs = []

    for year, month in MONTHS:
        df = download_month(year, month)
        if df is not None:
            out_path = os.path.join(OUTPUT_DIR, f"{SYMBOL}_{INTERVAL}_{year}-{month:02d}.csv")
            df.to_csv(out_path, index=False)
            all_dfs.append(df)

    if not all_dfs:
        print("No se descargó ningún mes. Revisa la configuración (símbolo/intervalo/meses).")
        return

    combined = pd.concat(all_dfs, ignore_index=True)

    # open_time viene en milisegundos epoch; añadimos columna legible
    combined["open_time_dt"] = pd.to_datetime(combined["open_time"], unit="ms")
    combined = combined.sort_values("open_time").reset_index(drop=True)

    final_path = os.path.join(OUTPUT_DIR, FINAL_CSV)
    combined.to_csv(final_path, index=False)

    print(f"\nListo. {len(combined)} velas combinadas guardadas en: {final_path}")
    print(f"Rango: {combined['open_time_dt'].min()} -> {combined['open_time_dt'].max()}")


if __name__ == "__main__":
    main()
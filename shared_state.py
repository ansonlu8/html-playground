import json
import os
from datetime import datetime

WATCHLIST_FILE = "watchlist.json"
STATUS_FILE = "bot_status.json"


def load_data(file_path, default):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def normalize_symbol(symbol):
    return symbol.strip().upper()


def load_watchlist():
    data = load_data(WATCHLIST_FILE, {"symbols": ["BTC-USD", "ETH-USD", "SOL-USD", "NVDA"]})
    symbols = [normalize_symbol(sym) for sym in data.get("symbols", []) if sym]
    return {"symbols": sorted(dict.fromkeys(symbols))}


def save_watchlist(symbols):
    save_data(WATCHLIST_FILE, {"symbols": symbols})


def load_status():
    return load_data(STATUS_FILE, {"equity": "0.00", "buying_power": "0.00", "positions": [], "last_update": "N/A"})


def save_status(equity, buying_power, positions, last_update=None):
    payload = {
        "equity": f"{equity:.2f}",
        "buying_power": f"{buying_power:.2f}",
        "positions": positions,
        "last_update": last_update or datetime.now().strftime("%H:%M:%S")
    }
    save_data(STATUS_FILE, payload)

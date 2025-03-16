# src/config.py
import json
import os

def load_river_config(filename="rivers.json"):
    # Ermittle den Pfad zur JSON-Datei im Ordner "config"
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", filename)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Konfigurationsdatei {config_path} nicht gefunden!")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("rivers", [])

if __name__ == "__main__":
    rivers = load_river_config()
    for river in rivers:
        print(f"Name: {river['name']}, Schwellenwert: {river.get('default_threshold')}")

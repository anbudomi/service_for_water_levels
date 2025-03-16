import json
import os
import time

def load_config(config_path="config/water_level_config.json", retries=3, delay=1):
    for attempt in range(retries):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Erstelle das Mapping der Schwellenwerte
            config_threshold_map = {
                station["name"]: station.get("waterThresholds", {})
                for station in config.get("water_stations", [])
            }
            return config, config_threshold_map
        except json.decoder.JSONDecodeError as e:
            print(f"JSONDecodeError beim Laden der Konfiguration: {e}. Versuche es erneut in {delay} Sekunden...")
            time.sleep(delay)
    raise Exception("Konfigurationsdatei konnte nach mehreren Versuchen nicht geladen werden.")

def update_config(config_path="config/water_level_config.json"):
    """
    Aktualisiert die Konfiguration, z. B. wenn der Nutzer Änderungen vorgenommen hat.
    Diese Funktion wird separat aufgerufen, sodass der zeitintensive Teil (die Erfassung
    der Schwellenwerte) nicht in jedem Durchlauf des Hauptprozesses ausgeführt werden muss.
    """
    return load_config(config_path)

def save_config(config, config_path="config/water_level_config.json"):
    temp_path = config_path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    os.replace(temp_path, config_path)


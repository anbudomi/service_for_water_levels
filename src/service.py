import logging
from logging_config import setup_logging
setup_logging(log_file="service.log", level=logging.INFO)

import time
import os
import threading
from config_manager import load_config, update_config
from data_retriever import get_all_water_data
from driver_manager import get_web_driver
from config_watcher import start_config_watcher

# Globale Variablen für Konfiguration und deren Mapping
config_lock = threading.Lock()
global_config, global_threshold_map = None, None

def update_config_callback():
    global global_config, global_threshold_map
    new_config, new_threshold_map = update_config("config/water_level_config.json")
    with config_lock:
        global_config = new_config
        global_threshold_map = new_threshold_map
    logging.info("Konfiguration wurde aktualisiert.")

def check_for_warning(current_value, thresholds):
    critical_threshold = thresholds.get("HW100")
    return critical_threshold and current_value >= critical_threshold

def process_stations(config, config_threshold_map, driver):
    selected_stations = config.get("general_config", {}).get("selected_stations", None)
    poll_interval = config.get("general_config", {}).get("poll_interval_seconds", 300)
    
    data_url = config.get("general_config", {}).get("data_url")
    data = get_all_water_data(driver, data_url, filter_names=selected_stations)
    
    for entry in data:
        station_name = entry[0]
        try:
            current_value = int(entry[3].replace(" cm", "").strip())
        except Exception:
            current_value = None
        
        thresholds = config_threshold_map.get(station_name, {})
        if current_value is not None and check_for_warning(current_value, thresholds):
            logging.warning(f"WARNUNG: Station {station_name} überschreitet kritischen Wert: {current_value} cm")
        else:
            logging.info(f"Station {station_name} ist unkritisch: {current_value} cm")
    
    return poll_interval

if __name__ == "__main__":
    config_path = "config/water_level_config.json"
    # Initiales Laden der Konfiguration
    global_config, global_threshold_map = load_config(config_path)
    
    # Starte den Konfig-Watcher in einem separaten Thread
    observer = start_config_watcher(config_path, update_config_callback)
    
    # Initialisiere den WebDriver einmalig
    driver = get_web_driver()
    
    try:
        while True:
            # Hole eine aktuelle Kopie der Konfiguration unter Lock
            with config_lock:
                current_config = global_config
                current_threshold_map = global_threshold_map
            poll_interval = process_stations(current_config, current_threshold_map, driver)
            logging.info(f"Warte {poll_interval} Sekunden bis zum nächsten Abruf...")
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        logging.info("Service wird beendet...")
    finally:
        driver.quit()
        observer.stop()
        observer.join()

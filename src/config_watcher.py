# src/config_watcher.py
import os
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, config_path, update_callback, debounce_interval=2):
        self.config_path = config_path
        self.update_callback = update_callback
        self.debounce_interval = debounce_interval
        self.last_modified = 0

    def on_modified(self, event):
        # Prüfe, ob es sich um die Konfigurationsdatei handelt
        if event.src_path.endswith(os.path.basename(self.config_path)):
            current_time = time.time()
            # Debounce: Nur auslösen, wenn seit dem letzten Trigger genügend Zeit vergangen ist
            if current_time - self.last_modified < self.debounce_interval:
                return
            self.last_modified = current_time
            logging.info("Konfigurationsdatei wurde geändert. Aktualisiere Konfiguration...")
            try:
                self.update_callback()
            except Exception as e:
                logging.error("Fehler beim Aktualisieren der Konfiguration: %s", e)

def start_config_watcher(config_path, update_callback):
    event_handler = ConfigFileHandler(config_path, update_callback)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(config_path), recursive=False)
    observer.start()
    return observer

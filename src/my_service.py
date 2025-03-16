import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import threading
import logging
import time
from config_manager import load_config, update_config
from driver_manager import get_web_driver
from data_retriever import get_all_water_data
from config_watcher import start_config_watcher
from service import process_stations  # Dein existierender Kern für die Datenverarbeitung

# Globaler Callback für den Watchdog
def update_config_callback():
    global global_config, global_threshold_map
    try:
        new_config, new_threshold_map = update_config("config/water_level_config.json")
        with config_lock:
            global_config = new_config
            global_threshold_map = new_threshold_map
        logging.info("Konfiguration wurde aktualisiert.")
    except Exception as e:
        logging.error("Fehler beim Aktualisieren der Konfiguration: %s", e)

# Globale Variablen für Konfiguration und deren Mapping
config_lock = threading.Lock()
global_config, global_threshold_map = None, None

def run_service():
    """
    Führt die Kernlogik des Dienstes aus – ohne pywin32-spezifische Startmechanismen.
    Dies ist der Code, der im Debug-Modus direkt ausgeführt wird.
    """
    config_path = "config/water_level_config.json"
    global global_config, global_threshold_map
    try:
        logging.info("Lade initiale Konfiguration...")
        global_config, global_threshold_map = load_config(config_path)
    except Exception as e:
        logging.error("Fehler beim Laden der Konfiguration: %s", e)
        return

    try:
        logging.info("Starte Konfig-Watcher...")
        observer = start_config_watcher(config_path, update_config_callback)
    except Exception as e:
        logging.error("Fehler beim Starten des Konfig-Watchers: %s", e)
        observer = None

    try:
        logging.info("Initialisiere WebDriver...")
        driver = get_web_driver()
    except Exception as e:
        logging.error("Fehler bei der WebDriver-Initialisierung: %s", e)
        return

    try:
        while True:
            with config_lock:
                current_config = global_config
                current_threshold_map = global_threshold_map
            poll_interval = process_stations(current_config, current_threshold_map, driver)
            logging.info(f"Warte {poll_interval} Sekunden bis zum nächsten Abruf...")
            time.sleep(poll_interval)
            try:
                global_config, global_threshold_map = update_config(config_path)
            except Exception as e:
                logging.error("Fehler beim Aktualisieren der Konfiguration: %s", e)
    except KeyboardInterrupt:
        logging.info("Debug-Service wird beendet...")
    finally:
        driver.quit()
        if observer:
            observer.stop()
            observer.join()

# Standard Windows-Dienst-Klasse
class WaterLevelService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WaterLevelService"
    _svc_display_name_ = "Service for Water Levels"
    _svc_description_ = "Überwacht Wasserstände und löst Warnungen aus, wenn Schwellen überschritten werden."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.main_thread = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)
        if self.main_thread:
            self.main_thread.join()
        logging.info("Service gestoppt.")

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("WaterLevelService startet.")
        # Melde sofort den Dienststatus, damit Windows den Start erkennt
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        # Starte die Hauptlogik in einem separaten Thread
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.daemon = True
        self.main_thread.start()
        # Warte in kurzen Intervallen, damit Windows kontinuierlich informiert wird
        while self.running:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
            if rc == win32event.WAIT_OBJECT_0:
                break
        servicemanager.LogInfoMsg("WaterLevelService beendet.")

    def main(self):
        # Hier wird die gleiche Logik wie in run_service() ausgeführt
        config_path = "config/water_level_config.json"
        global global_config, global_threshold_map
        try:
            logging.info("Lade initiale Konfiguration...")
            global_config, global_threshold_map = load_config(config_path)
        except Exception as e:
            servicemanager.LogErrorMsg(f"Fehler beim Laden der Konfiguration: {e}")
            return

        try:
            logging.info("Starte Konfig-Watcher...")
            observer = start_config_watcher(config_path, update_config_callback)
        except Exception as e:
            servicemanager.LogErrorMsg(f"Fehler beim Starten des Konfig-Watchers: {e}")
            observer = None

        try:
            logging.info("Initialisiere WebDriver...")
            driver = get_web_driver()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Fehler bei der WebDriver-Initialisierung: {e}")
            return

        try:
            while self.running:
                with config_lock:
                    current_config = global_config
                    current_threshold_map = global_threshold_map
                poll_interval = process_stations(current_config, current_threshold_map, driver)
                servicemanager.LogInfoMsg(f"Abruf abgeschlossen. Warte {poll_interval} Sekunden bis zum nächsten Abruf...")
                # Kurze Warteintervalle, um den Status regelmäßig zu aktualisieren
                elapsed = 0
                while self.running and elapsed < poll_interval:
                    time.sleep(5)
                    elapsed += 5
                try:
                    global_config, global_threshold_map = update_config(config_path)
                except Exception as e:
                    servicemanager.LogErrorMsg(f"Fehler beim Aktualisieren der Konfiguration: {e}")
        except Exception as e:
            servicemanager.LogErrorMsg(f"Fehler im Hauptloop: {e}")
        finally:
            driver.quit()
            if observer:
                observer.stop()
                observer.join()

if __name__ == '__main__':
    # Überprüfe, ob das erste Argument "debug" ist, und starte dann direkt run_service()
    if len(sys.argv) > 1 and sys.argv[1].lower() == "debug":
        run_service()
    else:
        win32serviceutil.HandleCommandLine(WaterLevelService)

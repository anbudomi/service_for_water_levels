import win32serviceutil
import win32service
import win32event
import servicemanager
import time
from data_retriever import get_all_water_data

class WaterLevelService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WaterLevelService"
    _svc_display_name_ = "Service for Water Levels"
    _svc_description_ = "Überwacht Wasserstände und löst bei Überschreiten von Schwellenwerten Warnungen aus."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        # Beispiel: Führt alle 15 Minuten den Datenabruf aus
        url = "https://hochwasser.rlp.de/pegelliste/land"
        while self.running:
            try:
                # Hier kannst du deine Logik einbinden – z. B. Daten abrufen, Warnungen prüfen, etc.
                data = get_all_water_data(url)
                # Weiterverarbeitung, Logging, etc.
            except Exception as e:
                servicemanager.LogErrorMsg(f"Fehler im Service: {e}")
            # Warte 15 Minuten (900 Sekunden) oder nutze einen Scheduler
            time.sleep(900)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(WaterLevelService)

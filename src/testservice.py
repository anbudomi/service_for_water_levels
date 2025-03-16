# src/minimal_service.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import time

class MinimalService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MinimalService"
    _svc_display_name_ = "Minimal Service"
    _svc_description_ = "Ein minimaler Testdienst, der nur einen Heartbeat ausgibt."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)
        servicemanager.LogInfoMsg("MinimalService gestoppt.")

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("MinimalService startet.")
        # Sofort den Status melden
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        # Schleife mit kurzen Warteintervallen
        while self.running:
            rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)
            if rc == win32event.WAIT_OBJECT_0:
                break
        servicemanager.LogInfoMsg("MinimalService beendet.")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MinimalService)

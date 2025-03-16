# testing.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_station_thresholds(station_href):
    """
    Öffnet den Detailbereich eines Gewässers (station_href), hängt '#pegelkennwerte' an 
    und extrahiert aus der Tabelle, die den Header "Wasserstandskennwerte" enthält, 
    die Schwellenwerte für:
      - HW 100
      - HW 50
      - HW 20
      - HW 2
      - MW
    Liefert ein Dictionary mit Schlüsseln ohne Leerzeichen (z. B. "HW100") und int-Werten.
    """
    BASE_URL = "https://hochwasser.rlp.de"
    if station_href.startswith("http"):
        station_url = station_href + "#pegelkennwerte"
    else:
        station_url = BASE_URL + station_href + "#pegelkennwerte"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(station_url)
    
    try:
        # Warte, bis mindestens eine Tabelle der gewünschten Klasse geladen ist
        tables = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.MuiTable-root.m-detail-measurementsites__table-wrapper"))
        )
    except Exception as e:
        print(f"Keine Tabelle gefunden für {station_url}: {e}")
        driver.quit()
        return {}
    
    target_table = None
    # Suche in allen gefundenen Tabellen nach dem Header "Wasserstandskennwerte"
    for table in tables:
        try:
            thead = table.find_element(By.CSS_SELECTOR, "thead")
            header_cells = thead.find_elements(By.TAG_NAME, "td")
            for cell in header_cells:
                if "Wasserstandskennwerte" in cell.text:
                    target_table = table
                    break
            if target_table:
                break
        except Exception as e:
            continue

    if not target_table:
        print(f"Keine Tabelle mit 'Wasserstandskennwerte' gefunden für {station_url}.")
        driver.quit()
        return {}
    
    thresholds = {}
    try:
        tbody = target_table.find_element(By.CSS_SELECTOR, "tbody.MuiTableBody-root")
        rows = tbody.find_elements(By.CSS_SELECTOR, "tr")
        if not rows:
            print(f"tbody gefunden, aber keine Zeilen in {station_url}. HTML: {tbody.get_attribute('innerHTML')}")
        valid_keys = ["HW 100", "HW 50", "HW 20", "HW 2", "MW"]
        valid_keys_nospace = [k.replace(" ", "") for k in valid_keys]
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                key_text = cells[0].text.strip()   # z. B. "HW 100" oder "HW100"
                value_text = cells[1].text.strip()  # z. B. "143 cm"
                print(f"DEBUG: Key cell: '{key_text}', Value cell: '{value_text}'")
                if key_text in valid_keys or key_text.replace(" ", "") in valid_keys_nospace:
                    key = key_text.replace(" ", "")
                    try:
                        value = int(value_text.replace(" cm", "").strip())
                    except Exception:
                        value = None
                    thresholds[key] = value
        if thresholds:
            print(f"Schwellenwerte für {station_url}: {thresholds}")
        else:
            print(f"Keine gültigen Schwellenwerte gefunden für {station_url}.")
    except Exception as e:
        print("Fehler beim Extrahieren der Schwellenwerte:", e)
    
    driver.quit()
    return thresholds

if __name__ == "__main__":
    # Test für die Station 'Abentheuer'
    station_href = "/flussgebiet/nahe/abentheuer"
    thresholds = get_station_thresholds(station_href)
    print(f"Thresholds for {station_href}: {thresholds}")

import os
import json
from data_retriever import get_all_water_data
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_station_thresholds(driver, station_href):
    """
    Öffnet den Detailbereich eines Gewässers (station_href) mit dem übergebenen driver,
    hängt '#pegelkennwerte' an und extrahiert aus der Tabelle, die den Header 
    "Wasserstandskennwerte" enthält, die Schwellenwerte für:
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
    
    driver.get(station_url)
    
    try:
        # Warte, bis mindestens eine Tabelle der gewünschten Klasse geladen ist
        tables = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.MuiTable-root.m-detail-measurementsites__table-wrapper"))
        )
    except Exception as e:
        print(f"Keine Tabelle gefunden für {station_url}: {e}")
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
    
    return thresholds

def create_json_config(url, filter_names=None, output_filename="water_level_config.json", collect_thresholds=True):
    """
    Ruft alle Stationen über get_all_water_data ab (erwartet 7-teilige Tupel) und ergänzt
    für jeden Eintrag (optional) die Schwellenwerte aus der Detailseite.
    Zusätzlich wird eine allgemeine Konfiguration (z. B. Abfrageintervall, ausgewählte Stationen)
    gespeichert.
    
    Mit dem Parameter collect_thresholds kann gesteuert werden, ob für jede Station
    die zeitintensive Schwellenwert-Abfrage durchgeführt wird (True) oder nicht (False).
    """
    # data: Liste von Tupeln (name, riverName, riverAreaName, yLast, xLast, catchmentArea, href)
    data = get_all_water_data(url, filter_names)
    
    # Optional: Einmalig (und nur wenn collect_thresholds True ist) soll ein WebDriver erstellt werden,
    # der für alle Detailseiten wiederverwendet wird.
    if collect_thresholds:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver = None
    
    water_stations = []
    for entry in data:
        if collect_thresholds and driver is not None:
            thresholds = get_station_thresholds(driver, entry[6])
        else:
            thresholds = {}  # Leeres Dict, wenn keine Schwellenwerte abgefragt werden sollen
        station = {
            "name": entry[0],
            "riverName": entry[1],
            "riverAreaName": entry[2],
            "catchmentArea": entry[5],
            "waterThresholds": thresholds
        }
        water_stations.append(station)
        print(f"Station '{entry[0]}' wurde verarbeitet.")
    
    if driver is not None:
        driver.quit()
    
    # Allgemeine Konfiguration: Hier kannst du weitere Parameter hinzufügen,
    # wie polling-Intervall, Benachrichtigungseinstellungen etc.
    general_config = {
        "poll_interval_seconds": 300,
        "data_url": url,
        "selected_stations": filter_names or []
    }
    
    json_config = {
        "water_stations": water_stations,
        "general_config": general_config
    }
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "config", output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_config, f, indent=4, ensure_ascii=False)
    
    print(f"JSON-Konfiguration wurde in '{output_path}' gespeichert.")

if __name__ == "__main__":
    # Beispiel-Aufruf: Erstelle die initiale Konfiguration mit vollständiger Schwellenwertabfrage
    url = "https://hochwasser.rlp.de/pegelliste/land"
    # Hier können die vom Nutzer gewünschten Stationen als Liste übergeben werden; 
    # ist None, werden alle Stationen abgerufen.
    selected_stations = []
    create_json_config(url, filter_names=selected_stations, collect_thresholds=True)

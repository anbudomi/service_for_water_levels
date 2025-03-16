import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_all_water_data(url, filter_names=None):
    """
    Ruft alle Wasserstandsdaten von der Seite ab.
    Wenn filter_names (Liste) übergeben wird, werden nur die Zeilen erfasst,
    deren Name in filter_names enthalten ist.
    
    Es wird ein Tuple zurückgegeben mit:
    (name, riverName, riverAreaName, yLast, xLast, catchmentArea, href)
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Headless-Modus: keine GUI öffnen
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(url)
    time.sleep(1)  # Kurze Wartezeit, bis die Seite initial geladen ist

    water_data = []

    while True:
        try:
            # Warte, bis alle Zeilen sichtbar sind
            WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, "MuiDataGrid-row"))
            )
        except Exception as e:
            print("Timeout oder Fehler beim Warten auf die Zeilen:", e)
            break

        rows = driver.find_elements(By.CLASS_NAME, "MuiDataGrid-row")
        for row in rows:
            try:
                # 1. Name (mit Link)
                name_elem = row.find_element(By.CSS_SELECTOR, 'div[data-field="name"] a')
                name = name_elem.text
                href = name_elem.get_attribute("href")  # Neuer Link als 7. Element
                
                # Falls ein Filter angegeben wurde, überspringe Zeilen, die nicht passen.
                if filter_names and name not in filter_names:
                    continue

                # 2. riverName
                river_name = row.find_element(By.CSS_SELECTOR, 'div[data-field="riverName"]').text
                # 3. riverAreaName (verschachteltes Div; nutze title, falls vorhanden, sonst Text)
                river_area_element = row.find_element(By.CSS_SELECTOR, 'div[data-field="riverAreaName"] div.MuiDataGrid-cellContent')
                river_area = river_area_element.get_attribute("title") or river_area_element.text
                # 4. yLast (letzter Messwert)
                y_last = row.find_element(By.CSS_SELECTOR, 'div[data-field="yLast"]').text
                # 5. xLast (Zeitstempel)
                x_last = row.find_element(By.CSS_SELECTOR, 'div[data-field="xLast"]').text
                # 6. catchmentArea (Einzugsgebiet)
                catchment_area = row.find_element(By.CSS_SELECTOR, 'div[data-field="catchmentArea"]').text

                # Tuple mit 7 Elementen
                water_data.append((name, river_name, river_area, y_last, x_last, catchment_area, href))
            except Exception as e:
                print("Fehler beim Auslesen einer Zeile:", e)

        # Versuche, den "Nächste Seite"-Button zu finden und zu klicken
        try:
            # Suche das SVG-Icon und ermittle seinen klickbaren Vorfahren (<button> oder <a>)
            next_svg = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@data-testid='KeyboardArrowRightIcon']"))
            )
            next_button = next_svg.find_element(By.XPATH, "ancestor::*[self::button or self::a]")
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@data-testid='KeyboardArrowRightIcon']/ancestor::*[self::button or self::a]"))
            )
            next_button.click()
            # Warte, bis sich der Inhalt (z. B. die erste Zeile) ändert
            WebDriverWait(driver, 10).until(EC.staleness_of(rows[0]))
        except Exception as e:
            print("Pagination abgeschlossen oder Next-Button nicht mehr vorhanden:", e)
            break

    driver.quit()
    return water_data

if __name__ == "__main__":
    url = "https://hochwasser.rlp.de/pegelliste/land"  # URL der ersten Seite

    # Wenn du nur nach bestimmten Gewässern suchen möchtest,
    # übergebe hier eine Liste, z. B. ["Odenbach"].
    # Ist filter_names None oder eine leere Liste, werden alle Daten ausgegeben.
    filter_names = ["Odenbach"]
    
    all_data = get_all_water_data(url, filter_names)
    for idx, data in enumerate(all_data, start=1):
        name, river_name, river_area, y_last, x_last, catchment_area, href = data
        print(f"({idx}) Gewässer: {name}, Fluss: {river_name}, Gebiet: {river_area}, Letzter Messwert: {y_last}, Zeit: {x_last}, Einzugsgebiet: {catchment_area}, Link: {href}")

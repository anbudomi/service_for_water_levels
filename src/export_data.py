import os
import json
from data_retriever import get_all_water_data

def create_json_file(url, filter_names=None, output_filename="water_stations.json"):
    # Abrufen der Daten (Liste von Tupeln)
    data = get_all_water_data(url, filter_names)
    
    # Erstelle eine Liste von Dictionaries, wobei jeder Eintrag um "waterLevelThreshhold" ergänzt wird.
    water_stations = []
    for entry in data:
        station = {
            "name": entry[0],
            "riverName": entry[1],
            "riverAreaName": entry[2],
            "yLast": entry[3],
            "xLast": entry[4],
            "catchmentArea": entry[5],
            "waterLevelThreshhold": 100
        }
        water_stations.append(station)
    
    # Verpacke die Liste in ein Dictionary
    json_data = {"water_stations": water_stations}
    
    # Bestimme den Pfad zum config-Ordner
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "config", output_filename)
    
    # Schreibe die JSON-Daten in die Datei
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)
    
    print(f"JSON-Daten wurden in '{output_path}' gespeichert.")

if __name__ == "__main__":
    url = "https://hochwasser.rlp.de/pegelliste/land"
    # Hier kannst du filter_names auf z.B. ["Odenbach"] setzen oder None übergeben, um alle zu exportieren.
    create_json_file(url, filter_names=None)

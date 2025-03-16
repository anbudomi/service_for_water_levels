import sys, os
# Füge den absoluten Pfad zum src-Ordner hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest
import json
from config_manager import load_config

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Temporäre Konfigurationsdatei erstellen
        self.test_config_path = "tests/test_water_level_config.json"
        test_config = {
            "data_url": "https://example.com/data",
            "selected_stations": ["Odenbach", "Abentheuer"],
            "general_config": {"poll_interval_seconds": 300},
            "water_stations": [
                {
                    "name": "Odenbach",
                    "riverName": "Testfluss",
                    "riverAreaName": "Testgebiet",
                    "catchmentArea": "20 km²",
                    "waterThresholds": {"HW100": 150, "HW50": 140, "HW20": 130, "HW2": 95, "MW": 40}
                }
            ]
        }
        with open(self.test_config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=4, ensure_ascii=False)

    def tearDown(self):
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def test_load_config(self):
        config, threshold_map = load_config(self.test_config_path)
        self.assertIn("data_url", config)
        self.assertIn("general_config", config)
        self.assertIn("water_stations", config)
        self.assertIn("Odenbach", threshold_map)
        self.assertEqual(threshold_map["Odenbach"].get("HW100"), 150)

if __name__ == "__main__":
    unittest.main()

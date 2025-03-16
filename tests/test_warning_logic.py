# tests/test_warning_logic.py
import unittest
import sys, os
# Füge den Projektstamm hinzu (der Ordner, der "src" enthält)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.service import check_for_warning


class TestWarningLogic(unittest.TestCase):
    def test_warning_triggered(self):
        # Angenommen, HW100 ist 150 und der aktuelle Wert beträgt 160
        thresholds = {"HW100": 150}
        self.assertTrue(check_for_warning(160, thresholds))

    def test_warning_not_triggered(self):
        thresholds = {"HW100": 150}
        self.assertFalse(check_for_warning(140, thresholds))

if __name__ == "__main__":
    unittest.main()

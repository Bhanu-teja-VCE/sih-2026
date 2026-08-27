"""
tests/test_multimodal.py
Evaluation tests for the Multimodal Parser and Excel Ingestion Engine.
Verifies parsing of input inspection spreadsheets and P&ID JSON metadata.
"""

import os
import unittest
from harness.multimodal_parser import MultimodalParser


class TestMultimodalParser(unittest.TestCase):

    def setUp(self):
        self.parser = MultimodalParser()
        self.demo_xlsx = "data/sample_boiler_inspection_data.xlsx"
        if not os.path.exists(self.demo_xlsx):
            self.parser.create_demo_inspection_excel(self.demo_xlsx)

    def test_parse_excel_inspection_report(self):
        data = self.parser.parse_excel_inspection_report(self.demo_xlsx)

        self.assertEqual(data["equipment_tag"], "B-101-Crude-Furnace-Tube")
        self.assertEqual(data["design_pressure_mpa"], 4.0)
        self.assertEqual(data["outer_diameter_mm"], 219.1)
        self.assertEqual(data["allowable_stress_mpa"], 137.0)
        self.assertEqual(data["measured_thickness_mm"], 7.48)
        self.assertGreaterEqual(len(data["grid_readings_mm"]), 16)

    def test_parse_pid_metadata(self):
        pid_file = "data/sample_pid_metadata.json"
        data = self.parser.parse_pid_metadata(pid_file)

        self.assertEqual(data["plant_id"], "MRPL-CDU-1")
        self.assertEqual(data["equipment"][0]["tag"], "B-101")
        self.assertTrue(any(i["tag"] == "PT-1044" for i in data["instrumentation"]))
        self.assertEqual(data["safety_interlocks"][0]["interlock_id"], "I-101")


if __name__ == "__main__":
    unittest.main()

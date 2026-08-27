"""
tests/test_deliverables.py
Evaluation tests for the PSU Deliverable Synthesizer.
Verifies valid generation of Microsoft Word (.docx) approval notes and Excel (.xlsx) sheets.
"""

import os
import unittest
from harness.types import PSUApprovalNote
from harness.deliverable_engine import DeliverableEngine


class TestDeliverableEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DeliverableEngine(output_dir="deliverables")

    def test_generate_docx_approval_note(self):
        note = PSUApprovalNote(
            subject="Approval for Continued Service Life of CDU-1 Furnace Coil B-101",
            equipment_tag="B-101-Crude-Furnace-Tube",
            background="Routine ultrasonic thickness testing was performed during the annual plant overhaul.",
            inspection_findings="Minimum wall thickness recorded: 7.48 mm across 16 test grid points.",
            calculation_summary="ASME B31.3 Code calculations confirm 5.2 years of remaining safe operational life.",
            financial_implication="INR 45,00,000/- proposed for routine retubing in FY 2028-29 overhaul plan.",
            authority_dop="Item 4.2(b) of MRPL Delegation of Power.",
            recommendation="Approval requested for continued operation with re-inspection after 24 months."
        )

        doc_path = self.engine.generate_docx_approval_note(note, filename="Test_MRPL_Approval_Note.docx")

        self.assertTrue(os.path.exists(doc_path))
        self.assertGreater(os.path.getsize(doc_path), 500)

    def test_generate_xlsx_calculation_sheet(self):
        calc_data = {
            "standard": "ASME_B31_3",
            "design_pressure_mpa": 4.0,
            "outer_diameter_mm": 219.1,
            "allowable_stress_mpa": 137.0,
            "required_min_thickness_mm": 6.2,
            "measured_thickness_mm": 7.48,
            "safe_margin_mm": 1.28,
            "annual_corrosion_rate_mm_yr": 0.25,
            "remaining_life_years": 5.12,
            "status": "APPROVED_SAFE"
        }

        xlsx_path = self.engine.generate_xlsx_calculation_sheet(calc_data, filename="Test_ASME_Calculations.xlsx")

        self.assertTrue(os.path.exists(xlsx_path))
        self.assertGreater(os.path.getsize(xlsx_path), 500)

    def test_generate_achievement_certificate_png_and_pdf(self):
        from harness.certificate_generator import generate_certificate
        res = generate_certificate(
            deliverables_dir="deliverables",
            output_png_name="Test_Certificate.png",
            output_pdf_name="Test_Certificate.pdf",
            extracted_metrics={
                "required_min_thickness_mm": 6.162,
                "measured_thickness_mm": 7.480,
                "remaining_life_years": 5.27
            }
        )
        self.assertTrue(os.path.exists(res["png_path"]))
        self.assertTrue(os.path.exists(res["pdf_path"]))
        self.assertGreater(os.path.getsize(res["png_path"]), 5000)
        self.assertGreater(os.path.getsize(res["pdf_path"]), 5000)
        self.assertTrue(res["certificate_id"].startswith("MRPL-SAI-POE-"))


if __name__ == "__main__":
    unittest.main()

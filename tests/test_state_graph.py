"""
tests/test_state_graph.py
Evaluation tests for the Multi-Branch Deterministic State Graph DAG Engine.
Verifies task-specific DAG branch execution across all 4 TaskIntents:
- VISION_INSPECTION
- CODE_GEN
- DOCUMENT_RAG
- REASONING_MEMO
"""

import unittest
from harness.types import TaskIntent
from harness.state_graph import StateGraphEngine


class TestStateGraphEngine(unittest.TestCase):

    def setUp(self):
        self.engine = StateGraphEngine()

    def test_vision_inspection_branch(self):
        prompt = "Read the attached boiler ultrasonic inspection report for B-101 and draft approval note"
        attached = ["sample_inspection_report.txt"]

        state = self.engine.execute_workflow(
            raw_prompt=prompt,
            attached_files=attached,
            mock_extracted_data={
                "equipment_tag": "B-101-Crude-Furnace-Tube",
                "design_pressure_mpa": 4.0,
                "outer_diameter_mm": 219.1,
                "allowable_stress_mpa": 137.0,
                "measured_thickness_mm": 7.48,
                "annual_corrosion_rate_mm": 0.25,
                "corrosion_allowance_mm": 3.0,
            }
        )

        self.assertTrue(state.is_completed)
        self.assertEqual(state.task_intent, TaskIntent.VISION_INSPECTION)
        self.assertGreaterEqual(len(state.plan), 3)
        self.assertGreaterEqual(len(state.tool_results), 1)
        self.assertTrue(state.tool_results[0].success)
        self.assertIn("approval_note_data", state.extracted_metrics)
        self.assertIsNotNone(state.root_hash)

    def test_code_gen_branch(self):
        prompt = "Write a Python script to calculate heat exchanger LMTD and thermal duty in sandbox"
        state = self.engine.execute_workflow(raw_prompt=prompt)

        self.assertTrue(state.is_completed)
        self.assertEqual(state.task_intent, TaskIntent.CODE_GEN)
        self.assertIn("sandbox_code", state.extracted_metrics)
        self.assertIn("sandbox_output", state.extracted_metrics)
        self.assertGreaterEqual(len(state.tool_results), 1)
        self.assertTrue(state.tool_results[0].success)

    def test_document_rag_branch(self):
        prompt = "What are the emergency turnaround procurement limits according to refinery SOP handbook?"
        state = self.engine.execute_workflow(raw_prompt=prompt)

        self.assertTrue(state.is_completed)
        self.assertEqual(state.task_intent, TaskIntent.DOCUMENT_RAG)
        self.assertIn("guidance_memo", state.extracted_metrics)
        self.assertIn("retrieved_sop_clauses", state.extracted_metrics)

    def test_reasoning_memo_branch(self):
        prompt = "Draft an administrative approval memo for routine maintenance overhaul under DOP guidelines"
        state = self.engine.execute_workflow(raw_prompt=prompt)

        self.assertTrue(state.is_completed)
        self.assertEqual(state.task_intent, TaskIntent.REASONING_MEMO)
        self.assertIn("approval_note_data", state.extracted_metrics)


if __name__ == "__main__":
    unittest.main()

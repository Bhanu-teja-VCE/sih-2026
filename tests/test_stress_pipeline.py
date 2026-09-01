"""
tests/test_stress_pipeline.py
Adversarial Stress-Testing Suite for Sovereign Industrial AI Workbench.
Tests edge cases, malicious AST payloads, empty/corrupted inputs, regex injection,
and end-to-end API resilience under extreme conditions.
"""

import os
import json
import tempfile
import unittest
from fastapi.testclient import TestClient

from api.server import app
from harness.types import TaskIntent
from harness.state_graph import StateGraphEngine
from harness.sandbox import CalculationSandbox
from harness.sovereign_rag import SovereignRAG
from harness.audit_ledger import ImmutableAuditLedger
from harness.semantic_router import SemanticRouter
from harness.deliverable_engine import DeliverableEngine


class TestPipelineStressSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.engine = StateGraphEngine()
        cls.sandbox = CalculationSandbox(default_timeout_seconds=2.0)
        cls.router = SemanticRouter()

    @classmethod
    def tearDownClass(cls):
        cls.engine.ledger.reset()

    # =========================================================================
    # 1. SANDBOX ADVERSARIAL STRESS TESTS (Security & Evasion Checks)
    # =========================================================================
    def test_sandbox_evasion_getattr_builtins(self):
        """Attempts to bypass AST by accessing builtins via getattr/attributes."""
        payload = 'g = getattr(__builtins__, "exec")\ng("print(1)")'
        res = self.sandbox.execute(payload)
        self.assertFalse(res.success)
        self.assertIn("Security Violation", res.error)

    def test_sandbox_evasion_dunder_subclasses(self):
        """Attempts sandbox breakout via object.__subclasses__ reflection."""
        payload = '[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == "catch_warnings"]'
        res = self.sandbox.execute(payload)
        self.assertTrue(res.success or "Security Violation" in str(res.error))

    def test_sandbox_recursion_and_memory_bomb(self):
        """Tests deep recursion stack overflow protection."""
        payload = "def f(): return f()\nf()"
        res = self.sandbox.execute(payload)
        self.assertFalse(res.success)
        self.assertIn("RecursionError", res.error)

    def test_sandbox_empty_and_whitespace_code(self):
        """Tests blank / whitespace code snippets."""
        res = self.sandbox.execute("   \n\t  ")
        self.assertTrue(res.success)
        self.assertEqual(res.output, "")

    def test_sandbox_unicode_and_special_characters(self):
        """Tests scripts with non-ASCII unicode math symbols (π, λ, σ)."""
        payload = 'import json\nprint(json.dumps({"stress_σ_mpa": 137.0, "pi_π": 3.14159}))'
        res = self.sandbox.execute(payload)
        self.assertTrue(res.success)
        self.assertIsInstance(res.output, dict)
        self.assertEqual(res.output["stress_σ_mpa"], 137.0)

    # =========================================================================
    # 2. RAG REGEX & CORRUPTED INPUT STRESS TESTS
    # =========================================================================
    def test_rag_special_regex_characters_query(self):
        """Queries containing unescaped regex meta-characters [ ] ( ) * + ?."""
        rag = SovereignRAG()
        rag.add_document("doc1", "Refinery furnace emergency shutdown threshold is 450 degrees Celsius.")
        
        res = rag.search("emergency shutdown [threshold] (450+)? *", top_k=3)
        self.assertGreater(len(res), 0)
        self.assertEqual(res[0]["doc_id"], "doc1")

    def test_rag_empty_query_and_empty_corpus(self):
        """RAG behavior when queried on empty index or empty string."""
        empty_rag = SovereignRAG()
        self.assertEqual(empty_rag.search(""), [])
        self.assertEqual(empty_rag.search("refinery boiler"), [])

    # =========================================================================
    # 3. SEMANTIC ROUTER RESILIENCE TESTS
    # =========================================================================
    def test_router_empty_and_garbage_prompts(self):
        """Empty string or pure punctuation prompts."""
        intent1, model1, _ = self.router.route("")
        self.assertEqual(intent1, TaskIntent.REASONING_MEMO)

        intent2, model2, _ = self.router.route("!@#$%^&*()_+{}|:<>?")
        self.assertEqual(intent2, TaskIntent.REASONING_MEMO)

    def test_router_case_insensitivity(self):
        """Upper/Mixed case keywords."""
        intent, model, _ = self.router.route("PARSE BOILER ULTRASONIC NDT INSPECTION REPORT WITH ASMe FORMULA")
        self.assertEqual(intent, TaskIntent.VISION_INSPECTION)

    # =========================================================================
    # 4. STATE GRAPH MULTI-INTENT END-TO-END STRESS TESTS
    # =========================================================================
    def test_state_graph_missing_attached_files(self):
        """Workflow execution when attached file paths do not exist on disk."""
        state = self.engine.execute_workflow(
            raw_prompt="Read inspection report for boiler B-101 and draft approval note",
            attached_files=["non_existent_folder/missing_file.xlsx"]
        )
        self.assertTrue(state.is_completed)
        self.assertIsNotNone(state.root_hash)
        self.assertIn("Minimum design thickness required", state.extracted_metrics.get("approval_note_data", {}).get("calculation_summary", ""))
        self.assertEqual(state.extracted_metrics.get("sandbox_output", {}).get("status"), "APPROVED_SAFE")

    def test_state_graph_equipment_tag_with_special_slashes(self):
        """Equipment tags containing slashes (e.g. B-101/A) shouldn't crash file paths."""
        state = self.engine.execute_workflow(
            raw_prompt="Perform inspection on B-101/A furnace coil",
            mock_extracted_data={"equipment_tag": "B-101/A-Furnace-Coil", "design_pressure_mpa": 4.0, "outer_diameter_mm": 219.1}
        )
        self.assertTrue(state.is_completed)
        self.assertIn("docx_filename", state.extracted_metrics)
        self.assertTrue(os.path.exists(os.path.join("deliverables", state.extracted_metrics["docx_filename"])))

    # =========================================================================
    # 5. FASTAPI API ADVERSARIAL ENDPOINT TESTS
    # =========================================================================
    def test_api_workflow_all_four_intents(self):
        """Stress-tests the full FastAPI /api/workflow/execute endpoint across all 4 intents."""
        prompts = [
            ("Read boiler ultrasonic report and draft approval note", TaskIntent.VISION_INSPECTION),
            ("Write a Python script to calculate heat exchanger LMTD", TaskIntent.CODE_GEN),
            ("Search SOP handbook for turnaround financial limits", TaskIntent.DOCUMENT_RAG),
            ("Draft administrative justification memo for CAPEX approval", TaskIntent.REASONING_MEMO),
        ]
        for prompt_text, expected_intent in prompts:
            res = self.client.post("/api/workflow/execute", json={"prompt": prompt_text, "attached_files": []})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["task_intent"], expected_intent.value)
            self.assertTrue(data["is_completed"])
            self.assertIsNotNone(data["root_hash"])

    def test_api_ledger_disk_verification_lifecycle(self):
        """Tests that /api/ledger/verify-disk-artifacts returns valid status after a workflow run."""
        # 1. Reset ledger and generate fresh deliverables
        self.client.post("/api/ledger/reset")
        self.client.post("/api/workflow/execute", json={
            "prompt": "Read boiler inspection report and generate approval note",
            "attached_files": []
        })
        
        # 2. Verify on-disk files
        res = self.client.get("/api/ledger/verify-disk-artifacts")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_valid"])
        self.assertGreaterEqual(data["total_files_checked"], 1)


if __name__ == "__main__":
    unittest.main()

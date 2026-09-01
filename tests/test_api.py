"""
tests/test_api.py
Evaluation tests for the FastAPI Sovereign Backend Server.
Verifies all REST API endpoints, custom file upload sanitization, egress testing,
local chat, ledger tampering, dashboard, and deliverable downloads.
"""

import os
import io
import unittest
from fastapi.testclient import TestClient
from api.server import app


class TestFastAPIServer(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_serve_dashboard(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("MANGALORE REFINERY", res.text)
        self.assertIn("Sovereign On-Premise Agentic AI Workbench", res.text)

    def test_serve_team_guide(self):
        res = self.client.get("/guide")
        self.assertEqual(res.status_code, 200)
        self.assertIn("TEAM MASTER KNOWLEDGE PORTAL", res.text)
        self.assertIn("Where is AI Actually Used", res.text)

    def test_get_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SOVEREIGN_CORE_ONLINE")
        self.assertTrue(data["airgapped"])
        self.assertEqual(data["wan_egress_packets"], 0)

    def test_get_airgap_status(self):
        res = self.client.get("/api/airgap/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("is_airgapped", data)
        self.assertIn("external_egress_violations_count", data)

    def test_airgap_egress_test_and_reset(self):
        # Trigger simulated egress test
        res = self.client.post("/api/airgap/test-egress")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "EGRESS_VIOLATION_TRIGGERED")

        # Verify status now reports violation
        status_res = self.client.get("/api/airgap/status")
        status_data = status_res.json()
        self.assertFalse(status_data["is_airgapped"])
        self.assertGreaterEqual(status_data["external_egress_violations_count"], 1)

        # Reset back to clean airgap
        reset_res = self.client.post("/api/airgap/reset")
        self.assertEqual(reset_res.status_code, 200)
        self.assertEqual(reset_res.json()["status"], "AIRGAP_RESTORED_CLEAN")

    def test_local_chat_endpoint(self):
        self.client.post("/api/airgap/reset")
        res = self.client.post("/api/local/chat", json={"prompt": "Calculate ASME B31.3 pipe wall thickness in Python"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue("asme" in data["local_response"].lower() or len(data["local_response"]) > 20)
        self.assertEqual(data["wan_packets_logged"], 0)
        self.assertTrue(data["is_airgapped"])
        self.assertIn("model_used", data)
        self.assertIn("intent_detected", data)

        # Test greeting conversational intent
        res_greet = self.client.post("/api/local/chat", json={"prompt": "hello"})
        self.assertEqual(res_greet.status_code, 200)
        self.assertTrue(len(res_greet.json()["local_response"]) > 10)

        # Test multimodal image chat intent (routed to Qwen2-VL-7B)
        tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        res_img = self.client.post("/api/local/chat", json={
            "prompt": "Inspect P&ID valve tags in this image",
            "images": [tiny_png]
        })
        self.assertEqual(res_img.status_code, 200)
        img_data = res_img.json()
        self.assertEqual(img_data["intent_detected"], "VISION_INSPECTION")
        self.assertIn("Qwen2-VL", img_data["model_used"])
        self.assertTrue(img_data["has_images"])

    def test_ledger_tamper_test_and_reset(self):
        payload = {
            "prompt": "Inspect boiler tube B-101 and draft approval note",
            "attached_files": ["sample_inspection_report.txt"]
        }
        self.client.post("/api/workflow/execute", json=payload)

        # Trigger tampering
        tamper_res = self.client.post("/api/ledger/tamper-test")
        self.assertEqual(tamper_res.status_code, 200)
        tamper_data = tamper_res.json()
        self.assertEqual(tamper_data["status"], "TAMPERING_SUCCESSFULLY_CAUGHT_BY_MERKLE_PROOF")
        self.assertFalse(tamper_data["verification_result"]["is_valid"])

        # Reset ledger
        reset_res = self.client.post("/api/ledger/reset")
        self.assertEqual(reset_res.status_code, 200)
        self.assertEqual(reset_res.json()["status"], "LEDGER_RESET_CLEAN")

    def test_router_classify_endpoint(self):
        res = self.client.post("/api/router/classify", json={"prompt": "Write python code to compute ASME wall thickness"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("intent", data)
        self.assertIn("selected_model", data)

    def test_sandbox_execute_endpoint(self):
        res = self.client.post("/api/sandbox/execute", json={"python_code": "print(100 * 2)", "timeout_seconds": 3.0})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["output"], 200)

    def test_custom_file_upload_and_path_traversal_protection(self):
        # 1. Normal safe file upload
        test_file = io.BytesIO(b"Tag,Thickness\nB-101,7.2")
        files = {"file": ("custom_report.csv", test_file, "text/csv")}
        res = self.client.post("/api/upload", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["filename"], "custom_report.csv")
        self.assertTrue(os.path.exists(data["file_path"]))

        # 2. Path traversal attack attempt (../../evil.txt)
        malicious_file = io.BytesIO(b"evil content")
        files_bad = {"file": ("../../evil.txt", malicious_file, "text/plain")}
        res_bad = self.client.post("/api/upload", files=files_bad)
        self.assertEqual(res_bad.status_code, 200)
        data_bad = res_bad.json()
        # Ensure path traversal was stripped and confined strictly inside uploads/
        self.assertEqual(data_bad["filename"], "evil.txt")
        self.assertFalse(".." in data_bad["file_path"])
        self.assertTrue(data_bad["file_path"].startswith("uploads"))

    def test_workflow_execute_and_deliverable_download(self):
        payload = {
            "prompt": "Evaluate ultrasonic thickness data for Crude Column C-101 and draft approval note",
            "attached_files": []
        }
        res = self.client.post("/api/workflow/execute", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_completed"])
        self.assertIn("deliverables", data)
        self.assertIn("docx_url", data["deliverables"])
        self.assertIn("xlsx_url", data["deliverables"])

        # Test deliverable download
        docx_name = data["deliverables"]["docx_filename"]
        dl_res = self.client.get(f"/api/deliverables/download/{docx_name}")
        self.assertEqual(dl_res.status_code, 200)
        self.assertGreater(len(dl_res.content), 0)

    def test_list_models(self):
        res = self.client.get("/api/models")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("models", data)
        self.assertGreaterEqual(len(data["models"]), 3)


if __name__ == "__main__":
    unittest.main()

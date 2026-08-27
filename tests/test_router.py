"""
tests/test_router.py
Automated evaluation tests for the Poly-Model Semantic Router.
Verifies model auto-selection across diverse industrial task types.
Supports both unittest and pytest natively.
"""

import unittest
from harness.types import TaskIntent, ModelRole, ModelConfig, WorkbenchState
from harness.semantic_router import SemanticRouter


class TestSemanticRouter(unittest.TestCase):

    def test_router_code_intent(self):
        router = SemanticRouter()
        prompt = "Write a Python script to calculate the minimum required pipe wall thickness according to ASME B31.3"
        intent, model, rationale = router.route(prompt)

        self.assertEqual(intent, TaskIntent.CODE_GEN)
        self.assertEqual(model.role, ModelRole.CODER)
        self.assertIn("Qwen", model.name)

    def test_router_vision_intent(self):
        router = SemanticRouter()
        prompt = "Check the valve status and flow direction in this attached drawing"
        attached = ["pid_distillation_unit_101.png"]
        intent, model, rationale = router.route(prompt, attached_files=attached)

        self.assertEqual(intent, TaskIntent.VISION_INSPECTION)
        self.assertEqual(model.role, ModelRole.VISION)
        self.assertTrue("VL" in model.name or "Vision" in model.name)

    def test_router_sop_rag_intent(self):
        router = SemanticRouter()
        prompt = "Look up the standard operating procedure (SOP) for emergency flare stack shutdown"
        intent, model, rationale = router.route(prompt)

        self.assertEqual(intent, TaskIntent.DOCUMENT_RAG)
        self.assertEqual(model.role, ModelRole.REASONER)

    def test_router_approval_memo_intent(self):
        router = SemanticRouter()
        prompt = "Draft a formal approval note for the procurement of boiler replacement tubes for the Chief General Manager"
        intent, model, rationale = router.route(prompt)

        self.assertEqual(intent, TaskIntent.REASONING_MEMO)
        self.assertEqual(model.role, ModelRole.REASONER)
        self.assertTrue("DeepSeek" in model.name or "Reasoner" in model.name)

    def test_router_pluggable_registration(self):
        router = SemanticRouter()
        custom_model = ModelConfig(
            name="Custom-Refinery-Llama-70B",
            model_id="custom-refinery:70b",
            role=ModelRole.REASONER,
            context_window=32768,
            endpoint_url="http://192.168.1.150:11434"
        )
        router.register_model(custom_model)

        prompt = "Prepare a board meeting summary on refinery yield optimization"
        intent, model, _ = router.route(prompt)

        self.assertEqual(model.name, "Custom-Refinery-Llama-70B")
        self.assertEqual(model.endpoint_url, "http://192.168.1.150:11434")

    def test_router_state_enrichment(self):
        router = SemanticRouter()
        state = WorkbenchState(
            raw_prompt="Calculate boiler corrosion rate over 5 years in Python",
            attached_files=[]
        )
        enriched = router.route_state(state)

        self.assertEqual(enriched.task_intent, TaskIntent.CODE_GEN)
        self.assertIsNotNone(enriched.selected_model)
        self.assertEqual(enriched.selected_model.role, ModelRole.CODER)


if __name__ == "__main__":
    unittest.main()

"""
harness/semantic_router.py
Poly-Model Semantic Router for Sovereign Industrial AI Workbench.
Dynamically routes user tasks to the optimal open-weight SLM in <10ms.
"""

import os
from typing import List, Optional, Tuple, Dict
from harness.types import TaskIntent, ModelRole, ModelConfig, WorkbenchState

# Configurable via environment variable:
#   set OLLAMA_HOST=https://mba-love-rebate-watch.trycloudflare.com
#   or set OLLAMA_HOST=http://192.168.1.X:11434
_DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://mba-love-rebate-watch.trycloudflare.com")


class SemanticRouter:
    """
    Sub-10ms Intent Classifier & Poly-Model Selector.
    Prevents single-model bloat by matching specialized SLMs to industrial task types.
    """

    def __init__(self, lan_inference_host: str = _DEFAULT_OLLAMA_HOST):
        self.lan_host = lan_inference_host
        self.model_registry: Dict[ModelRole, ModelConfig] = {
            ModelRole.CODER: ModelConfig(
                name="Qwen-2.5-Coder-7B",
                model_id="qwen2.5-coder:7b",
                role=ModelRole.CODER,
                context_window=16384,
                temperature=0.0,
                endpoint_url=self.lan_host,
            ),
            ModelRole.VISION: ModelConfig(
                name="Qwen2-VL-7B",
                model_id="qwen2-vl:7b",
                role=ModelRole.VISION,
                context_window=8192,
                temperature=0.1,
                endpoint_url=self.lan_host,
            ),
            ModelRole.REASONER: ModelConfig(
                name="DeepSeek-R1-Distill-8B",
                model_id="deepseek-r1:8b",
                role=ModelRole.REASONER,
                context_window=16384,
                temperature=0.2,
                endpoint_url=self.lan_host,
            ),
        }

    def register_model(self, model: ModelConfig) -> None:
        """Pluggable adapter: Allows dropping in new open-weight models without redesign."""
        self.model_registry[model.role] = model

    def route(self, prompt: str, attached_files: Optional[List[str]] = None) -> Tuple[TaskIntent, ModelConfig, str]:
        """
        Classifies task intent and selects the optimal specialized model.
        Returns: (TaskIntent, ModelConfig, routing_rationale)
        """
        files = attached_files or []
        prompt_lower = prompt.lower()

        # 1. Vision & Document Inspection Check (P&ID drawings, scanned logs, inspection reports)
        vision_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".pdf"}
        has_visual_file = any(any(f.lower().endswith(ext) for ext in vision_extensions) for f in files)
        inspection_file = any("inspection" in f.lower() or "report" in f.lower() or "pid" in f.lower() for f in files)
        visual_keywords = ["p&id", "drawing", "diagram", "scanned", "schematic", "photograph", "image", "valve layout", "inspection report", "ultrasonic"]

        if has_visual_file or inspection_file or any(k in prompt_lower for k in visual_keywords):
            return (
                TaskIntent.VISION_INSPECTION,
                self.model_registry[ModelRole.VISION],
                "Detected engineering drawing / inspection document. Routed to specialized Multimodal Vision SLM.",
            )

        # 2. Code Generation & Engineering Math Check
        code_keywords = [
            "python", "script", "code", "function", "parse", "asme", "barlow",
            "calculation", "formula", "corrosion rate", "stress", "wall thickness",
            "algorithm", "regex", "sql", "automate", "unit test", "simulation"
        ]
        if any(k in prompt_lower for k in code_keywords):
            return (
                TaskIntent.CODE_GEN,
                self.model_registry[ModelRole.CODER],
                "Detected programming / engineering mathematical logic. Routed to Code Synthesis SLM.",
            )

        # 3. Document Search & SOP Knowledge Grounding Check
        rag_keywords = ["sop", "standard operating procedure", "manual", "handbook", "past correspondence", "circular"]
        if any(k in prompt_lower for k in rag_keywords):
            return (
                TaskIntent.DOCUMENT_RAG,
                self.model_registry[ModelRole.REASONER],
                "Detected refinery manual / SOP knowledge lookup. Routed to Sovereign RAG Grounding Engine.",
            )

        # 4. Default: PSU Formal Reasoning / Approval Notes
        return (
            TaskIntent.REASONING_MEMO,
            self.model_registry[ModelRole.REASONER],
            "Detected formal administrative / approval memo drafting. Routed to Deep Reasoning SLM.",
        )

    def route_state(self, state: WorkbenchState) -> WorkbenchState:
        """Enriches the centralized WorkbenchState with intent and model selection."""
        intent, model, rationale = self.route(state.raw_prompt, state.attached_files)
        state.task_intent = intent
        state.selected_model = model
        return state

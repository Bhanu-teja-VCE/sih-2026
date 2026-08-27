"""
harness/types.py
Pydantic Schemas and Type Definitions for Sovereign Industrial AI Workbench (MRPL PS 26117).
Deterministic state management, tool contracts, and verifiable ledger schemas.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time
import uuid


class TaskIntent(str, Enum):
    """Classified industrial task intents."""
    VISION_INSPECTION = "VISION_INSPECTION"  # Scanned NDT logs, P&ID schematics, visual inspection
    CODE_GEN = "CODE_GEN"                    # Python calculation scripts, sandbox math execution
    DOCUMENT_RAG = "DOCUMENT_RAG"            # Internal SOP retrieval, refinery manuals
    REASONING_MEMO = "REASONING_MEMO"        # Multi-tier PSU Approval Notes, Delegation of Power


class ModelRole(str, Enum):
    """Specialized roles for open-weight Small Language Models (SLMs)."""
    CODER = "CODER"          # e.g., Qwen-2.5-Coder-7B
    VISION = "VISION"        # e.g., Qwen2-VL-7B
    REASONER = "REASONER"    # e.g., DeepSeek-R1-Distill-8B


class ModelConfig(BaseModel):
    """Configuration contract for registered open-weight models."""
    name: str = Field(description="Display name e.g. Qwen-2.5-Coder-7B")
    model_id: str = Field(description="Ollama / vLLM model tag e.g. qwen2.5-coder:7b")
    role: ModelRole = Field(description="Specialized architectural role")
    context_window: int = Field(default=8192, description="Max token context window")
    temperature: float = Field(default=0.1, description="Inference temperature")
    endpoint_url: str = Field(default="http://127.0.0.1:11434", description="Local inference socket")


class ToolType(str, Enum):
    """Available local deterministic tools."""
    OCR_PARSER = "OCR_PARSER"
    EXCEL_INGESTOR = "EXCEL_INGESTOR"
    SANDBOX_CALCULATOR = "SANDBOX_CALCULATOR"
    SOP_VECTOR_STORE = "SOP_VECTOR_STORE"
    DOCX_GENERATOR = "DOCX_GENERATOR"
    XLSX_GENERATOR = "XLSX_GENERATOR"


class ToolCallResult(BaseModel):
    """Standardized output schema for all local sandbox/tool executions."""
    tool_name: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class PSUApprovalNote(BaseModel):
    """Formal PSU approval note format matching MRPL Delegation of Power (DOP) structure."""
    subject: str = Field(description="Clear administrative approval subject line")
    equipment_tag: str = Field(description="Refinery equipment tag e.g. B-101-Furnace-Tube")
    background: str = Field(description="Context and operational background")
    inspection_findings: str = Field(description="Summary of ultrasonic/visual inspection")
    calculation_summary: str = Field(description="ASME code verification and remaining life")
    financial_implication: str = Field(description="Cost estimate in INR / budgetary allocation")
    authority_dop: str = Field(description="Delegation of Power (DOP) schedule reference")
    recommendation: str = Field(description="Final action requested for GM/Director approval")
    approver_name: str = Field(default="Chief General Manager (Technical)", description="Signatory title")
    designation: str = Field(default="MRPL Refinery Operations", description="Department")


class WorkbenchState(BaseModel):
    """
    Centralized, deterministic memory state for the Agentic DAG.
    Decoupled from model text output to eliminate state corruption.
    """
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    raw_prompt: str = Field(description="Original user prompt or query")
    attached_files: List[str] = Field(default_factory=list, description="File paths to attached images/PDFs")
    
    # Routing & Model Selection
    task_intent: Optional[TaskIntent] = None
    selected_model: Optional[ModelConfig] = None
    
    # State Graph Planning & Step Execution
    plan: List[str] = Field(default_factory=list, description="Multi-step execution plan")
    current_step_index: int = 0
    
    # Data extraction & calculations
    extracted_metrics: Dict[str, Any] = Field(default_factory=dict, description="Parsed physical measurements")
    tool_results: List[ToolCallResult] = Field(default_factory=list, description="History of tool invocations")
    
    # Circuit Breaker & Safety
    retry_count: int = 0
    max_retries: int = 3
    error_log: List[str] = Field(default_factory=list, description="Captured execution error stack traces")
    
    # Deliverable Outputs & Cryptographic Merkle State
    deliverable_path: Optional[str] = None
    root_hash: Optional[str] = Field(default=None, description="Cryptographic SHA-256 Merkle root hash")
    proof_certificate: Optional[str] = Field(default=None, description="Proof-of-Execution ASCII Certificate")
    is_completed: bool = False
    start_timestamp: float = Field(default_factory=time.time)

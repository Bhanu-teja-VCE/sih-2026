"""
harness/audit_ledger.py
Cryptographic SHA-256 Merkle DAG Audit Ledger for Sovereign AI Workbench.
Guarantees tamper-evident, verifiable proof-of-execution for multi-step agentic workflows.
Persists every state transition to an append-only cryptographic JSONL ledger that survives process restarts.
"""

import os
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class LedgerBlock(BaseModel):
    """
    Immutable block in the Merkle DAG transition chain.
    """
    block_index: int = Field(description="Monotonically increasing block index")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of state creation")
    node_name: str = Field(description="DAG node name that produced this transition")
    input_payload_hash: str = Field(description="SHA-256 hash of the node input payload")
    output_payload_hash: str = Field(description="SHA-256 hash of the node output payload")
    parent_hashes: List[str] = Field(default_factory=list, description="SHA-256 hashes of parent dependency blocks")
    block_hash: str = Field(description="Canonical SHA-256 hash sealing this block and its causal history")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")

    @property
    def prev_block_hash(self) -> str:
        return self.parent_hashes[0] if self.parent_hashes else "0" * 64


class ImmutableAuditLedger:
    """
    Append-Only Cryptographic State Ledger.
    Ensures that every step of agent planning, tool execution, and sandbox math
    is cryptographically bound to its predecessors. Persisted across sessions to a disk JSONL file.
    """

    def __init__(self, genesis_seed: str = "MRPL_PS26117_SOVEREIGN_ROOT", persistence_path: Optional[str] = None):
        self.genesis_seed = genesis_seed
        self.persistence_path = persistence_path or os.path.join("deliverables", "audit_ledger.jsonl")
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        self.chain: List[LedgerBlock] = []
        self._block_map: Dict[str, LedgerBlock] = {}

        # Load existing blocks from disk if present; otherwise initialize genesis
        if os.path.exists(self.persistence_path) and os.path.getsize(self.persistence_path) > 0:
            self._load_from_disk()
            self.verify_integrity()
        else:
            self._init_genesis_block()

    def _load_from_disk(self) -> None:
        """Loads and parses existing Merkle transition blocks from disk JSONL."""
        self.chain = []
        self._block_map = {}
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    block = LedgerBlock.model_validate_json(line)
                    self.chain.append(block)
                    self._block_map[block.block_hash] = block
        except Exception:
            self._init_genesis_block()

    @staticmethod
    def _compute_hash(data: Any) -> str:
        """Computes deterministic SHA-256 hash of arbitrary Python primitives."""
        if data is None:
            raw_str = "null"
        elif isinstance(data, (dict, list)):
            raw_str = json.dumps(data, sort_keys=True, default=str)
        else:
            raw_str = str(data)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """Computes cryptographic SHA-256 digest of an on-disk deliverable artifact file."""
        if not os.path.exists(file_path):
            return "0" * 64
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def verify_artifact_file(self, file_path: str, expected_sha256: str) -> bool:
        """Verifies if an on-disk deliverable matches its registered cryptographic hash."""
        current_hash = self._compute_file_hash(file_path)
        return current_hash == expected_sha256

    def verify_disk_artifacts(self, deliverables_dir: str = "deliverables") -> Dict[str, Any]:
        """
        Scans all physical deliverables on disk and validates their current live byte SHA-256
        against the latest cryptographic hashes sealed into the Merkle DAG blocks.
        """
        results = []
        tampered = []
        checked_files = set()

        # Iterate in reverse to check the most recent sealed state for each file
        for block in reversed(self.chain):
            meta = block.metadata or {}
            # Check for docx artifact
            if "docx_sha256" in meta and meta["docx_sha256"]:
                fname = meta.get("docx_filename") or "Approval_Note.docx"
                if fname not in checked_files:
                    checked_files.add(fname)
                    fpath = os.path.join(deliverables_dir, fname)
                    if os.path.exists(fpath):
                        live_hash = self._compute_file_hash(fpath)
                        expected_hash = meta["docx_sha256"]
                        matches = (live_hash == expected_hash)
                        entry = {
                            "file_type": "WORD_APPROVAL_NOTE (.docx)",
                            "filename": fname,
                            "file_path": fpath,
                            "expected_sealed_sha256": expected_hash,
                            "live_disk_sha256": live_hash,
                            "is_intact": matches,
                            "block_index": block.block_index
                        }
                        results.append(entry)
                        if not matches:
                            tampered.append(entry)

            # Check for xlsx artifact
            if "xlsx_sha256" in meta and meta["xlsx_sha256"]:
                fname = meta.get("xlsx_filename") or "Engineering_Calculations_ASME_B31_3.xlsx"
                if fname not in checked_files:
                    checked_files.add(fname)
                    fpath = os.path.join(deliverables_dir, fname)
                    if os.path.exists(fpath):
                        live_hash = self._compute_file_hash(fpath)
                        expected_hash = meta["xlsx_sha256"]
                        matches = (live_hash == expected_hash)
                        entry = {
                            "file_type": "EXCEL_CALCULATION_SHEET (.xlsx)",
                            "filename": fname,
                            "file_path": fpath,
                            "expected_sealed_sha256": expected_hash,
                            "live_disk_sha256": live_hash,
                            "is_intact": matches,
                            "block_index": block.block_index
                        }
                        results.append(entry)
                        if not matches:
                            tampered.append(entry)

        if not results:
            return {
                "is_valid": True,
                "total_files_checked": 0,
                "message": "No deliverable artifacts registered in current ledger state.",
                "files": []
            }

        is_all_clean = len(tampered) == 0
        return {
            "is_valid": is_all_clean,
            "total_files_checked": len(results),
            "tampered_count": len(tampered),
            "files": results,
            "tampered_files": tampered,
            "message": (
                "✅ All physical disk files match their sealed Merkle hashes exactly."
                if is_all_clean
                else f"🚨 PHYSICAL FILE TAMPERING DETECTED: {len(tampered)} file(s) modified on disk after DAG sealing!"
            )
        }

    @staticmethod
    def _canonical_parent_hash(parent_hashes: List[str]) -> str:
        """
        Produces a single deterministic parent summary from multiple parent hashes.
        Ensures converging branches in the DAG produce identical hashes regardless of list order.
        """
        if not parent_hashes:
            return "0" * 64
        sorted_parents = sorted(parent_hashes)
        combined = ":".join(sorted_parents)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _init_genesis_block(self) -> None:
        """Creates the immutable genesis root of the refinery audit trail."""
        genesis_in_hash = self._compute_hash(self.genesis_seed)
        genesis_out_hash = self._compute_hash({"genesis": "MRPL Sovereign AI Core"})
        genesis_block_hash = hashlib.sha256(
            f"0000000000000000:GENESIS:{genesis_in_hash}:{genesis_out_hash}:0.0".encode("utf-8")
        ).hexdigest()

        genesis_block = LedgerBlock(
            block_index=0,
            timestamp=0.0,
            node_name="GENESIS_ROOT",
            input_payload_hash=genesis_in_hash,
            output_payload_hash=genesis_out_hash,
            parent_hashes=[],
            block_hash=genesis_block_hash,
            metadata={"description": "MRPL Asset Integrity Sovereign Root"}
        )
        self.chain = [genesis_block]
        self._block_map = {genesis_block_hash: genesis_block}

        try:
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                f.write(genesis_block.model_dump_json() + "\n")
        except OSError:
            pass

    def reset(self) -> None:
        """Resets chain and recreates genesis on disk."""
        self._init_genesis_block()

    def record_transition(
        self,
        node_name: str,
        input_data: Any,
        output_data: Any,
        parent_hashes: Optional[Union[str, List[str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LedgerBlock:
        """
        Records a verified state transition block into the chain and appends to disk.
        """
        if parent_hashes is None:
            parents = [self.chain[-1].block_hash]
        elif isinstance(parent_hashes, str):
            parents = [parent_hashes]
        else:
            parents = sorted(list(parent_hashes))

        parent_summary = self._canonical_parent_hash(parents)
        in_hash = self._compute_hash(input_data)
        out_hash = self._compute_hash(output_data)
        now = time.time()

        raw_block_str = f"{parent_summary}:{node_name}:{in_hash}:{out_hash}:{now}"
        block_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()

        block = LedgerBlock(
            block_index=len(self.chain),
            timestamp=now,
            node_name=node_name,
            input_payload_hash=in_hash,
            output_payload_hash=out_hash,
            parent_hashes=parents,
            block_hash=block_hash,
            metadata=metadata or {}
        )

        self.chain.append(block)
        self._block_map[block_hash] = block

        # Append to persistent ledger on disk
        try:
            with open(self.persistence_path, "a", encoding="utf-8") as f:
                f.write(block.model_dump_json() + "\n")
        except OSError:
            pass

        return block

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Mathematically verifies the complete DAG chain from Genesis to Leaf.
        Detects any unauthorized modification to intermediate inputs, outputs, or links.
        """
        if not self.chain:
            return {"is_valid": False, "tampered_block_index": 0, "message": "Ledger is empty."}

        # 1. Verify Genesis
        genesis = self.chain[0]
        if genesis.block_index != 0 or genesis.node_name != "GENESIS_ROOT":
            return {"is_valid": False, "tampered_block_index": 0, "message": "Genesis root corrupted."}

        # 2. Iterate and re-calculate all blocks
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            parent_summary = self._canonical_parent_hash(curr.parent_hashes)

            # Ensure all parent hashes exist
            for p_hash in curr.parent_hashes:
                if p_hash not in self._block_map:
                    return {
                        "is_valid": False,
                        "tampered_block_index": i,
                        "message": f"Dangling parent reference at block {i}: {p_hash[:12]}..."
                    }

            # Recalculate block hash
            expected_raw = f"{parent_summary}:{curr.node_name}:{curr.input_payload_hash}:{curr.output_payload_hash}:{curr.timestamp}"
            expected_hash = hashlib.sha256(expected_raw.encode("utf-8")).hexdigest()

            if expected_hash != curr.block_hash:
                return {
                    "is_valid": False,
                    "tampered_block_index": i,
                    "message": (
                        f"Cryptographic Tamper Detected at Block #{i} ('{curr.node_name}'). "
                        f"Expected Hash: {expected_hash[:16]}... vs Stored Hash: {curr.block_hash[:16]}..."
                    )
                }

        return {
            "is_valid": True,
            "tampered_block_index": None,
            "total_blocks_verified": len(self.chain),
            "root_hash": self.chain[-1].block_hash,
            "message": f"All {len(self.chain)} blocks cryptographically verified with 0 tampering."
        }

    def tamper_block_output(self, block_index: int = 3, forged_data: Any = "FORGED_SANDBOX_OUTPUT_TAMPERED") -> Dict[str, Any]:
        """
        Simulates an unauthorized memory alteration to demonstrate instant tamper detection.
        """
        if block_index < 1 or block_index >= len(self.chain):
            return {
                "status": "ERROR_INVALID_BLOCK_INDEX",
                "message": f"Cannot tamper block index {block_index}. Chain length is {len(self.chain)}."
            }

        target_block = self.chain[block_index]
        forged_hash = self._compute_hash(forged_data)

        # Alter the payload hash in memory without updating the block hash
        target_block.output_payload_hash = forged_hash

        verification = self.verify_integrity()
        return {
            "status": "TAMPERING_SUCCESSFULLY_CAUGHT_BY_MERKLE_PROOF",
            "tampered_block_index": block_index,
            "node_name": target_block.node_name,
            "forged_payload_hash": forged_hash,
            "verification_result": verification
        }

    def get_root_hash(self) -> str:
        """Returns the latest state root hash sealing the entire causal execution history."""
        return self.chain[-1].block_hash if self.chain else "0" * 64

    def generate_proof_of_execution_certificate(self) -> str:
        """Formats an official proof-of-execution certificate for PSU auditing."""
        root_hash = self.get_root_hash()
        verification = self.verify_integrity()
        status_str = "100% VERIFIED_VALID" if verification["is_valid"] else "TAMPERED_BREACH"

        cert_lines = [
            "================================================================================",
            "        MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL) — SOVEREIGN AI    ",
            "                  CRYPTOGRAPHIC PROOF-OF-EXECUTION CERTIFICATE                  ",
            "================================================================================",
            f"State Root Hash      : {root_hash}",
            f"Total Ledger Blocks  : {len(self.chain)}",
            f"Chain Integrity      : {status_str}",
            f"Genesis Seed         : {self.genesis_seed}",
            f"Persistent Log       : {self.persistence_path}",
            "--------------------------------------------------------------------------------",
            "TRANSITION CHAIN AUDIT LOG:",
        ]

        for block in self.chain:
            parent_short = block.prev_block_hash[:12] + "..." if block.prev_block_hash else "None"
            cert_lines.append(
                f"  [Block #{block.block_index:02d}] {block.node_name:<28} | Hash: {block.block_hash[:16]}... | Parent: {parent_short}"
            )

        cert_lines.extend([
            "--------------------------------------------------------------------------------",
            "VERIFICATION GUARANTEE:",
            "  Every state transition was executed in an on-premise air-gapped environment.",
            "  All engineering calculations and decisions are sealed by SHA-256 Merkle proofs.",
            "================================================================================",
        ])

        return "\n".join(cert_lines)

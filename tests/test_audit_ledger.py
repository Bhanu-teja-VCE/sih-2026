"""
tests/test_audit_ledger.py
Evaluation tests for the Immutable Cryptographic Merkle DAG Audit Ledger.
Verifies SHA-256 block chaining, multi-parent DAG convergence, lexicographical sorting,
tamper detection simulation, and physical on-disk file checksum verification.
"""

import os
import tempfile
import unittest
from harness.audit_ledger import ImmutableAuditLedger


class TestAuditLedger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.persistence_path = os.path.join(self.temp_dir.name, "test_ledger.jsonl")
        self.ledger = ImmutableAuditLedger(persistence_path=self.persistence_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_genesis_and_chaining(self):
        self.assertEqual(len(self.ledger.chain), 1)
        self.assertEqual(self.ledger.chain[0].node_name, "GENESIS_ROOT")

        b1 = self.ledger.record_transition("NODE_1_ROUTER", {"input": "test"}, {"model": "Qwen"})
        self.assertEqual(b1.block_index, 1)
        self.assertEqual(b1.parent_hashes, [self.ledger.chain[0].block_hash])

        b2 = self.ledger.record_transition("NODE_2_SANDBOX", {"math": "ASME"}, {"status": "APPROVED"})
        self.assertEqual(b2.block_index, 2)
        self.assertEqual(b2.parent_hashes, [b1.block_hash])

        self.assertTrue(self.ledger.verify_integrity()["is_valid"])

    def test_persistence_across_restarts(self):
        """Verifies that an existing ledger JSONL is accurately reloaded upon restart."""
        # 1. Record 2 blocks
        b1 = self.ledger.record_transition("NODE_1_ROUTER", {"input": "initial"}, {"model": "Qwen"})
        b2 = self.ledger.record_transition("NODE_2_PLANNER", {"plan": [1, 2]}, {"status": "OK"})
        root_before = self.ledger.get_root_hash()
        self.assertEqual(len(self.ledger.chain), 3)

        # 2. Simulate process restart by instantiating a new ledger pointing to same path
        restarted_ledger = ImmutableAuditLedger(persistence_path=self.persistence_path)
        self.assertEqual(len(restarted_ledger.chain), 3)
        self.assertEqual(restarted_ledger.get_root_hash(), root_before)
        self.assertTrue(restarted_ledger.verify_integrity()["is_valid"])

    def test_multi_parent_dag_lexicographical_sorting(self):
        """Tests that converging parallel DAG branches produce deterministic canonical hashes."""
        b1 = self.ledger.record_transition("NODE_PARALLEL_OCR", {"doc": "excel"}, {"metrics": "parsed"})
        b2 = self.ledger.record_transition("NODE_PARALLEL_RAG", {"query": "SOP"}, {"sop": "retrieved"})

        converging_block = self.ledger.record_transition(
            node_name="NODE_CONVERGING_DELIVERABLE",
            input_data={"merged": True},
            output_data={"deliverable": "docx"},
            parent_hashes=[b2.block_hash, b1.block_hash]
        )

        self.assertEqual(converging_block.parent_hashes, sorted([b1.block_hash, b2.block_hash]))
        self.assertTrue(self.ledger.verify_integrity()["is_valid"])

    def test_tamper_detection(self):
        self.ledger.record_transition("NODE_1_ROUTER", {"input": "test"}, {"model": "Qwen"})
        self.ledger.record_transition("NODE_2_SANDBOX", {"math": "ASME"}, {"status": "APPROVED"})
        self.assertTrue(self.ledger.verify_integrity()["is_valid"])

        tamper_res = self.ledger.tamper_block_output(block_index=1, forged_data="TAMPERED_FORGED_CALCULATION")
        self.assertEqual(tamper_res["status"], "TAMPERING_SUCCESSFULLY_CAUGHT_BY_MERKLE_PROOF")
        self.assertFalse(self.ledger.verify_integrity()["is_valid"])
        self.assertEqual(self.ledger.verify_integrity()["tampered_block_index"], 1)

    def test_verify_disk_artifacts_clean_and_tampered(self):
        """Verifies physical on-disk file checksum validation and tamper catching."""
        file_path = os.path.join(self.temp_dir.name, "Engineering_Calculations_ASME_B31_3.xlsx")
        with open(file_path, "wb") as f:
            f.write(b"ORIGINAL_VALID_EXCEL_BYTE_CONTENT")

        file_hash = self.ledger._compute_file_hash(file_path)

        self.ledger.record_transition(
            node_name="NODE_5_DELIVERABLES",
            input_data={"file": "test"},
            output_data={"xlsx_filename": "Engineering_Calculations_ASME_B31_3.xlsx"},
            metadata={"xlsx_sha256": file_hash, "xlsx_filename": "Engineering_Calculations_ASME_B31_3.xlsx"}
        )

        # 1. Clean verification
        clean_audit = self.ledger.verify_disk_artifacts(deliverables_dir=self.temp_dir.name)
        self.assertTrue(clean_audit["is_valid"])
        self.assertEqual(clean_audit["tampered_count"], 0)

        # 2. Tamper file on disk (modify 1 byte)
        with open(file_path, "ab") as f:
            f.write(b"_FORGED_MODIFICATION")

        tampered_audit = self.ledger.verify_disk_artifacts(deliverables_dir=self.temp_dir.name)
        self.assertFalse(tampered_audit["is_valid"])
        self.assertEqual(tampered_audit["tampered_count"], 1)
        self.assertIn("PHYSICAL FILE TAMPERING DETECTED", tampered_audit["message"])

    def test_proof_of_execution_certificate(self):
        self.ledger.record_transition("NODE_1_ROUTER", {"input": "test"}, {"model": "Qwen"})
        cert = self.ledger.generate_proof_of_execution_certificate()
        self.assertIn("MANGALORE REFINERY", cert)
        self.assertIn("100% VERIFIED", cert)


if __name__ == "__main__":
    unittest.main()

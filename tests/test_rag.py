"""
tests/test_rag.py
Evaluation tests for Sovereign Local RAG Engine.
Verifies on-premise BM25 indexing, retrieval accuracy, and zero external dependency.
"""

import unittest
from harness.sovereign_rag import SovereignRAG


class TestSovereignRAG(unittest.TestCase):

    def setUp(self):
        self.rag = SovereignRAG(chunk_size=100, chunk_overlap=20)

    def test_indexing_and_search(self):
        doc = (
            "Section 14.2: For crude distillation furnaces and high-temperature transfer lines, "
            "a minimum nominal corrosion allowance of 3.0 mm must be maintained under ASME B31.3. "
            "Ultrasonic thickness testing indicates required retubing within 12 months if thickness drops below t_min."
        )
        chunks = self.rag.add_document("MRPL_SOP_Sec14", doc)
        self.assertGreaterEqual(chunks, 1)

        results = self.rag.search("corrosion allowance ASME B31.3", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["doc_id"], "MRPL_SOP_Sec14")
        self.assertIn("3.0 mm", results[0]["text"])
        self.assertGreater(results[0]["relevance_score"], 0.0)

    def test_load_sop_file(self):
        loaded = self.rag.load_file("data/refinery_sop_handbook.txt")
        self.assertGreaterEqual(loaded, 1)

        results = self.rag.search("Delegation of Power Chief General Manager approval", top_k=2)
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("Chief General Manager" in r["text"] or "DOP" in r["text"] for r in results))


if __name__ == "__main__":
    unittest.main()

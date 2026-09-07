"""Tests for Pre-Retrieval RAG Access Control and Document Filtering."""

import unittest
from rag.engine import RAG_ENGINE


class TestRAGSecurity(unittest.TestCase):
    def test_grade_1_cannot_retrieve_confidential_sop(self):
        # Grade 1 queries for safety interlock matrix (which is CONFIDENTIAL)
        res = RAG_ENGINE.search(
            query="safety interlock matrix emergency depressurization",
            role="GRADE_1",
            user_id="usr_op101",
        )
        self.assertTrue(res["success"])
        # Verify that no CONFIDENTIAL documents were retrieved
        for r in res["results"]:
            self.assertEqual(r["classification"], "PUBLIC_INTERNAL")
        self.assertGreater(res["security_metrics"]["docs_excluded_by_security_filter"], 0)

    def test_grade_3_can_retrieve_confidential_sop(self):
        # Grade 3 plant superintendent queries for safety interlock matrix
        res = RAG_ENGINE.search(
            query="safety interlock matrix emergency depressurization",
            role="GRADE_3",
            user_id="usr_super303",
        )
        self.assertTrue(res["success"])
        # Should include CONFIDENTIAL document
        classifications = [r["classification"] for r in res["results"]]
        self.assertIn("CONFIDENTIAL", classifications)

    def test_highly_confidential_excluded_from_standard_rag(self):
        # Even Grade 3 does not get HIGHLY_CONFIDENTIAL secret catalyst recipe in general search
        res = RAG_ENGINE.search(
            query="active zeolite platinum catalyst regeneration",
            role="GRADE_3",
            user_id="usr_super303",
        )
        for r in res["results"]:
            self.assertNotEqual(r["classification"], "HIGHLY_CONFIDENTIAL")


if __name__ == "__main__":
    unittest.main()

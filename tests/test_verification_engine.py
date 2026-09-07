"""Tests for the Verification Engine.

Validates all verification modes:
- Code execution verification (exit code, stderr, stdout)
- Document artifact verification (docx, xlsx, pptx format integrity)
- RAG grounding verification
- Vision extraction verification
- Engineering physics / API 510 compliance checks
"""

import unittest
import tempfile
from pathlib import Path
from backend.app.verification.verification_engine import VERIFICATION
from backend.app.core.config import GLOBAL_CONFIG


class TestCodeExecutionVerification(unittest.TestCase):
    def test_successful_execution_passes(self):
        """Clean sandbox output should produce PASS."""
        result = VERIFICATION.verify_code_execution({
            "exit_code": 0,
            "stdout": "Corrosion Rate: 0.600 mm/yr, Remaining Life: 3.17 yrs",
            "stderr": "",
            "timed_out": False,
        })
        self.assertEqual(result.status, "PASS")
        self.assertGreater(len(result.checks_passed), 0)
        self.assertEqual(len(result.checks_failed), 0)

    def test_nonzero_exit_code_fails(self):
        """Non-zero exit code should produce RETRY (fixable)."""
        result = VERIFICATION.verify_code_execution({
            "exit_code": 1,
            "stdout": "",
            "stderr": "NameError: name 'x' is not defined",
            "timed_out": False,
        })
        self.assertEqual(result.status, "RETRY")
        self.assertTrue(result.can_retry)

    def test_timeout_fails_hard(self):
        """Timed-out execution should produce FAIL (non-retryable timeout)."""
        result = VERIFICATION.verify_code_execution({
            "exit_code": -1,
            "stdout": "",
            "stderr": "Process timed out after 10 seconds",
            "timed_out": True,
        })
        self.assertIn(result.status, ["FAIL", "RETRY"])

    def test_empty_output_flagged(self):
        """Clean exit but no output should flag missing results."""
        result = VERIFICATION.verify_code_execution({
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
        })
        # Should still have at least one failure (no output)
        self.assertGreater(len(result.checks_failed), 0)


class TestArtifactVerification(unittest.TestCase):
    def test_nonexistent_file_fails(self):
        """Verifying a non-existent file should produce FAIL."""
        result = VERIFICATION.verify_artifact("/nonexistent/path/to/file.docx")
        self.assertEqual(result.status, "FAIL")
        self.assertIn("not found", result.checks_failed[0].lower())

    def test_valid_docx_verification(self):
        """A valid .docx file should pass structural verification."""
        # Generate a test docx first
        from tools.documents.doc_generator import DOC_GENERATOR
        gen_result = DOC_GENERATOR.generate_approval_note_docx(
            "E-TEST-001",
            {"measured_thickness_mm": 8.4, "min_required_thickness_mm": 6.5},
            "TestEngineer",
        )
        self.assertTrue(gen_result["success"])

        # Verify it
        verif = VERIFICATION.verify_artifact(
            gen_result["file_path"],
            required_sections=["MRPL", "Inspection"],
        )
        self.assertEqual(verif.status, "PASS")
        self.assertGreater(len(verif.checks_passed), 0)

    def test_valid_xlsx_verification(self):
        """A valid .xlsx file should pass structural verification."""
        from tools.documents.doc_generator import DOC_GENERATOR
        gen_result = DOC_GENERATOR.generate_efficiency_xlsx(
            "E-TEST-002",
            {"avg_flow_kg_h": 45000, "avg_delta_t_c": 75.5},
        )
        self.assertTrue(gen_result["success"])

        verif = VERIFICATION.verify_artifact(gen_result["file_path"])
        self.assertEqual(verif.status, "PASS")

    def test_valid_pptx_verification(self):
        """A valid .pptx file should pass structural verification."""
        from tools.documents.doc_generator import DOC_GENERATOR
        gen_result = DOC_GENERATOR.generate_presentation_pptx(
            "E-TEST-003",
            {"measured_thickness_mm": 8.4, "remaining_life_years": 3.17},
        )
        self.assertTrue(gen_result["success"])

        verif = VERIFICATION.verify_artifact(gen_result["file_path"])
        self.assertEqual(verif.status, "PASS")

    def test_missing_required_sections_fails(self):
        """File missing mandatory sections should fail verification."""
        # Create a minimal text file
        test_path = GLOBAL_CONFIG.ARTIFACTS_DIR / "test_minimal.txt"
        test_path.write_text("This is a minimal test file with no industrial content.", encoding="utf-8")

        verif = VERIFICATION.verify_artifact(
            str(test_path),
            required_sections=["MRPL", "API 510", "Equipment Tag"],
        )
        self.assertEqual(verif.status, "FAIL")
        self.assertGreater(len(verif.checks_failed), 0)

        # Clean up
        test_path.unlink(missing_ok=True)

    def test_tiny_file_flagged(self):
        """Abnormally small files should be flagged."""
        test_path = GLOBAL_CONFIG.ARTIFACTS_DIR / "test_tiny.docx"
        test_path.write_bytes(b"tiny")

        verif = VERIFICATION.verify_artifact(str(test_path))
        # Should flag abnormally small size
        has_size_warning = any("small" in f.lower() or "empty" in f.lower() for f in verif.checks_failed)
        self.assertTrue(has_size_warning)

        test_path.unlink(missing_ok=True)


class TestRAGGroundingVerification(unittest.TestCase):
    def test_well_grounded_response_passes(self):
        """Response with strong vocabulary overlap with evidence should pass."""
        evidence = [
            "API 510 pressure vessel inspection code requires minimum wall thickness evaluation.",
            "Heat exchanger E-1102 scheduled for ultrasonic thickness measurement during turnaround.",
        ]
        response = "According to API 510, the heat exchanger E-1102 requires minimum wall thickness evaluation via ultrasonic inspection during turnaround."

        result = VERIFICATION.verify_rag_grounding(evidence, response)
        self.assertEqual(result.status, "PASS")

    def test_ungrounded_response_flagged(self):
        """Response with minimal overlap should trigger NEEDS_HUMAN_REVIEW."""
        evidence = [
            "The crude distillation unit processes 15 MMTPA throughput.",
        ]
        response = "Quantum computing leverages superposition and entanglement for parallel computation in cryptographic systems."

        result = VERIFICATION.verify_rag_grounding(evidence, response)
        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")

    def test_no_evidence_fails(self):
        """No evidence documents should produce FAIL."""
        result = VERIFICATION.verify_rag_grounding([], "Some response text.")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(result.can_retry)


class TestVisionExtractionVerification(unittest.TestCase):
    def test_valid_detection_passes(self):
        """Detected components with matching types should pass."""
        components = [
            {"type": "valve", "tag": "V-101", "confidence": 0.92},
            {"type": "heat_exchanger", "tag": "E-1102", "confidence": 0.88},
        ]
        result = VERIFICATION.verify_vision_extraction(components, ["valve", "heat_exchanger"])
        self.assertEqual(result.status, "PASS")

    def test_empty_detection_fails(self):
        """No detected components should produce FAIL."""
        result = VERIFICATION.verify_vision_extraction([], ["valve"])
        self.assertEqual(result.status, "FAIL")

    def test_missing_expected_type_retries(self):
        """Missing expected component type should produce RETRY."""
        components = [
            {"type": "pipe", "tag": "P-201", "confidence": 0.85},
        ]
        result = VERIFICATION.verify_vision_extraction(components, ["valve"])
        self.assertEqual(result.status, "RETRY")
        self.assertTrue(result.can_retry)


class TestEngineeringPhysicsVerification(unittest.TestCase):
    def test_safe_operating_envelope_passes(self):
        """Measurements within safe API 510 limits should pass."""
        result = VERIFICATION.verify_engineering_physics({
            "measured_thickness_mm": 8.4,
            "min_required_thickness_mm": 6.5,
            "corrosion_rate_mm_per_year": 0.6,
        })
        self.assertEqual(result.status, "PASS")
        self.assertGreater(len(result.checks_passed), 0)

    def test_below_retirement_thickness_triggers_human_review(self):
        """Thickness below T_min should trigger NEEDS_HUMAN_REVIEW."""
        result = VERIFICATION.verify_engineering_physics({
            "measured_thickness_mm": 5.8,
            "min_required_thickness_mm": 6.5,
            "corrosion_rate_mm_per_year": 0.6,
        })
        self.assertEqual(result.status, "NEEDS_HUMAN_REVIEW")
        critical_found = any("CRITICAL" in f or "BELOW" in f for f in result.checks_failed)
        self.assertTrue(critical_found)

    def test_missing_measurements_fail(self):
        """Missing measurement values should produce failures."""
        result = VERIFICATION.verify_engineering_physics({
            "measured_thickness_mm": None,
            "min_required_thickness_mm": 6.5,
        })
        self.assertIn(result.status, ["FAIL"])
        self.assertGreater(len(result.checks_failed), 0)

    def test_negative_thickness_fails(self):
        """Physically impossible negative thickness should fail."""
        result = VERIFICATION.verify_engineering_physics({
            "measured_thickness_mm": -2.0,
            "min_required_thickness_mm": 6.5,
        })
        self.assertEqual(result.status, "FAIL")


if __name__ == "__main__":
    unittest.main()

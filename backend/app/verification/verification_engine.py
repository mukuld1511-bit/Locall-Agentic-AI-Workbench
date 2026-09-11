"""Standalone Verification Engine for Sovereign Industrial Operations.

Principle (Section 25 & 70):
Never declare success without verification.
Output statuses:
- PASS: Artifact and execution satisfy all physical, regulatory, and schema invariants.
- FAIL: Defect detected, non-zero exit code, corrupted format, or missing artifact.
- RETRY: Transient tool failure or fixable parameter error suitable for automated recovery.
- NEEDS_HUMAN_REVIEW: Ambiguous findings, severe anomalies, or parameter override requirements.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class VerificationResult:
    status: str  # PASS, FAIL, RETRY, NEEDS_HUMAN_REVIEW
    checks_passed: List[str]
    checks_failed: List[str]
    details: Dict[str, Any]
    can_retry: bool = False
    remediation_suggestion: Optional[str] = None


class VerificationEngine:
    def verify_code_execution(self, sandbox_result: Dict[str, Any]) -> VerificationResult:
        """Verifies output of sandboxed Python code execution."""
        passed = []
        failed = []

        # Check 1: Exit code
        if sandbox_result.get("exit_code") == 0 and not sandbox_result.get("timed_out"):
            passed.append("Exit code zero (clean termination)")
        else:
            failed.append(f"Non-zero exit code: {sandbox_result.get('exit_code')}")

        # Check 2: Stderr empty
        stderr = sandbox_result.get("stderr", "")
        if not stderr:
            passed.append("No stderr errors or tracebacks")
        else:
            failed.append(f"Stderr errors present: {stderr[:120]}")

        # Check 3: Stdout non-empty
        stdout = sandbox_result.get("stdout", "")
        if stdout:
            passed.append("Calculation emitted valid stdout results")
        else:
            failed.append("No output generated from calculation script")

        # Determine status
        if not failed:
            return VerificationResult(
                status="PASS",
                checks_passed=passed,
                checks_failed=[],
                details={"stdout": stdout},
            )
        else:
            # Check if retryable (e.g. syntax or runtime error in generated code)
            can_retry = "timed out" not in str(failed)
            return VerificationResult(
                status="RETRY" if can_retry else "FAIL",
                checks_passed=passed,
                checks_failed=failed,
                details={"stderr": stderr},
                can_retry=can_retry,
                remediation_suggestion="Prompt coding worker to fix variable types or missing definitions.",
            )

    def verify_artifact(self, file_path_str: str, required_sections: Optional[List[str]] = None) -> VerificationResult:
        """Verifies existence, integrity, non-zero size, and required sections of generated files."""
        file_path = Path(file_path_str)
        passed = []
        failed = []

        # Check 1: File exists on disk
        if file_path.exists():
            passed.append("Artifact file exists on filesystem")
        else:
            failed.append(f"File not found: {file_path_str}")
            return VerificationResult("FAIL", passed, failed, {"path": file_path_str}, can_retry=True)

        # Check 2: File size > 0
        size = file_path.stat().st_size
        if size > 100:
            passed.append(f"File size valid ({size} bytes)")
        else:
            failed.append(f"File is abnormally small or empty ({size} bytes)")

        # Check 3: Format validity & Required sections
        content_text = ""
        ext = file_path.suffix.lower()

        try:
            if ext == ".docx":
                import docx
                doc = docx.Document(file_path)
                passed.append("Valid Microsoft Word binary document structure (.docx)")
                # Extract text from paragraphs and tables
                p_text = " ".join(p.text for p in doc.paragraphs)
                t_text = " ".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
                content_text = p_text + " " + t_text
            elif ext == ".xlsx":
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True)
                passed.append("Valid Microsoft Excel binary workbook structure (.xlsx)")
                sheet_texts = []
                for sname in wb.sheetnames:
                    sheet = wb[sname]
                    for row in sheet.iter_rows(values_only=True):
                        sheet_texts.extend(str(v) for v in row if v is not None)
                content_text = " ".join(sheet_texts)
            elif ext == ".pptx":
                from pptx import Presentation
                prs = Presentation(file_path)
                passed.append("Valid PowerPoint presentation structure (.pptx)")
                slide_texts = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            slide_texts.append(shape.text_frame.text)
                content_text = " ".join(slide_texts)
            else:
                content_text = file_path.read_text(encoding="utf-8", errors="ignore")
                passed.append("Plain text / CSV readable format")
        except Exception as e:
            failed.append(f"Format corruption or parser error: {str(e)}")

        if required_sections and content_text:
            for sec in required_sections:
                if sec.lower() in content_text.lower():
                    passed.append(f"Required section/tag verified: '{sec}'")
                else:
                    failed.append(f"Missing mandatory section/tag: '{sec}'")

        status = "PASS" if not failed else "FAIL"
        return VerificationResult(
            status=status,
            checks_passed=passed,
            checks_failed=failed,
            details={"file_size": size, "path": str(file_path), "format": ext},
            can_retry=status == "FAIL",
        )

    def verify_rag_grounding(self, evidence_texts: List[str], response_text: str) -> VerificationResult:
        """Verifies that RAG response is grounded in retrieved local documentation evidence."""
        passed = []
        failed = []

        if not evidence_texts:
            failed.append("No source document evidence was retrieved for grounding check.")
            return VerificationResult("FAIL", passed, failed, {"evidence_count": 0}, can_retry=True)

        passed.append(f"Source documentation retrieved ({len(evidence_texts)} chunks)")

        # Verify key terms overlap
        import re
        resp_tokens = set(re.findall(r"\w{4,}", response_text.lower()))
        evidence_all = " ".join(evidence_texts).lower()

        grounded_tokens = [t for t in resp_tokens if t in evidence_all]
        grounding_ratio = len(grounded_tokens) / max(1, len(resp_tokens))

        if grounding_ratio >= 0.35:
            passed.append(f"Response vocabulary grounded in source evidence ({round(grounding_ratio * 100, 1)}% grounding)")
            status = "PASS"
        else:
            failed.append(f"Response shows low grounding overlap ({round(grounding_ratio * 100, 1)}%) with source SOPs")
            status = "NEEDS_HUMAN_REVIEW"

        return VerificationResult(
            status=status,
            checks_passed=passed,
            checks_failed=failed,
            details={"grounding_ratio": round(grounding_ratio, 3), "evidence_count": len(evidence_texts)},
        )

    def verify_vision_extraction(self, detected_components: List[Dict[str, Any]], expected_types: Optional[List[str]] = None) -> VerificationResult:
        """Verifies that vision extraction detected valid engineering diagram components."""
        passed = []
        failed = []

        if not detected_components:
            failed.append("No engineering components detected in diagram.")
            return VerificationResult("FAIL", passed, failed, {"detected_count": 0}, can_retry=True)

        passed.append(f"Detected {len(detected_components)} diagram components/tags")

        if expected_types:
            found_types = {str(c.get("type", "")).lower() for c in detected_components}
            for exp in expected_types:
                if exp.lower() in found_types:
                    passed.append(f"Expected component type verified: '{exp}'")
                else:
                    failed.append(f"Expected component type not detected: '{exp}'")

        status = "PASS" if not failed else "RETRY"
        return VerificationResult(
            status=status,
            checks_passed=passed,
            checks_failed=failed,
            details={"components_count": len(detected_components)},
            can_retry=status == "RETRY",
        )

    def verify_engineering_physics(self, findings: Dict[str, Any]) -> VerificationResult:
        """Verifies that engineering values are physically plausible and compliant with API 510."""
        passed = []
        failed = []

        thickness = findings.get("measured_thickness_mm")
        t_min = findings.get("min_required_thickness_mm")
        corrosion_rate = findings.get("corrosion_rate_mm_per_year")

        # Physically impossible measurement: hard failure.
        # Do this before the safety-threshold check below so negative
        # values are never misclassified as a human-review condition.
        if thickness is not None and thickness <= 0:
            failed.append(
                f"Measured thickness ({thickness} mm) is physically impossible; "
                "thickness must be greater than 0 mm."
            )
            return VerificationResult(
                status="FAIL",
                checks_passed=passed,
                checks_failed=failed,
                details={"measured": thickness, "t_min": t_min},
                can_retry=False,
            )

        if thickness is not None and thickness > 0:
            passed.append("Measured thickness is physically positive (>0mm)")
        else:
            failed.append("Measured thickness is non-positive or missing")

        if t_min is not None and t_min > 0:
            passed.append("Retirement thickness T_min is valid")
        else:
            failed.append("Retirement thickness T_min invalid")

        if thickness and t_min:
            if thickness < t_min:
                failed.append(f"CRITICAL SAFETY ALERT: Measured thickness ({thickness}mm) is BELOW minimum retirement thickness ({t_min}mm)!")
                return VerificationResult(
                    status="NEEDS_HUMAN_REVIEW",
                    checks_passed=passed,
                    checks_failed=failed,
                    details={"measured": thickness, "t_min": t_min},
                    remediation_suggestion="Immediate human inspection required. Shell de-rating or replacement mandatory.",
                )
            else:
                passed.append(f"Thickness {thickness}mm exceeds minimum threshold {t_min}mm (Safe Operating Envelope)")

        status = "PASS" if not failed else "FAIL"
        return VerificationResult(
            status=status,
            checks_passed=passed,
            checks_failed=failed,
            details=findings,
        )


VERIFICATION = VerificationEngine()

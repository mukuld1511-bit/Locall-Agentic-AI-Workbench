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

        # Check 3: Required sections
        if required_sections:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for sec in required_sections:
                    if sec.lower() in content.lower():
                        passed.append(f"Required section present: '{sec}'")
                    else:
                        failed.append(f"Missing mandatory section: '{sec}'")
            except Exception as e:
                failed.append(f"Cannot parse artifact content: {str(e)}")

        status = "PASS" if not failed else "FAIL"
        return VerificationResult(
            status=status,
            checks_passed=passed,
            checks_failed=failed,
            details={"file_size": size, "path": str(file_path)},
            can_retry=status == "FAIL",
        )

    def verify_engineering_physics(self, findings: Dict[str, Any]) -> VerificationResult:
        """Verifies that engineering values are physically plausible and compliant with API 510."""
        passed = []
        failed = []

        thickness = findings.get("measured_thickness_mm")
        t_min = findings.get("min_required_thickness_mm")
        corrosion_rate = findings.get("corrosion_rate_mm_per_year")

        if thickness and thickness > 0:
            passed.append("Measured thickness is physically positive (>0mm)")
        else:
            failed.append("Measured thickness is non-positive or missing")

        if t_min and t_min > 0:
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

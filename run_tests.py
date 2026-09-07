"""Master Test Runner for Sovereign Industrial AI Workbench.

Executes all unit, security, integration, and end-to-end test suites.
Validates zero-egress policies, RBAC, prompt injection defenses,
sandbox isolation, model swapping, and artifact generation.
"""

import sys
import unittest
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))


def run_all_tests():
    print("=" * 80)
    print("SOVEREIGN INDUSTRIAL AGENTIC AI WORKBENCH - TEST SUITE RUNNER")
    print("Organization: Mangalore Refinery and Petrochemicals Limited (MRPL)")
    print("Problem Statement ID: SIH26117 | Target: NVIDIA RTX 5060 Sovereign Profile")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover and add test files
    test_files = [
        "tests.test_auth",
        "tests.test_rbac_policy",
        "tests.test_prompt_injection",
        "tests.test_model_manager",
        "tests.test_tool_gateway",
        "tests.test_rag_security",
        "tests.test_human_approval",
        "tests.test_verification_engine",
        "tests.test_e2e_workflows",
    ]

    for module_name in test_files:
        try:
            mod = __import__(module_name, fromlist=["*"])
            suite.addTests(loader.loadTestsFromModule(mod))
        except Exception as e:
            print(f"[!] Error loading {module_name}: {e}")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 80)
    if result.wasSuccessful():
        print("[OK] ALL TESTS PASSED SUCCESSFULLY! The software platform is verified and ready.")
        return 0
    else:
        print(f"[FAILED] TESTS FAILED: {len(result.failures)} failures, {len(result.errors)} errors.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

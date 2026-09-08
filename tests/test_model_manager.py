"""Tests for Model Manager, RTX 5060 VRAM Budget Enforcement, and Model Swapping."""

import unittest
from model_manager.manager import MODEL_MGR


class TestModelManager(unittest.TestCase):
    def setUp(self):
        # Reset state
        MODEL_MGR.active_workers.clear()
        MODEL_MGR.load_worker("organizer")

    def test_vram_budget_limit(self):
        status = MODEL_MGR.get_system_status()
        self.assertLessEqual(status["vram_current_used_mb"], status["vram_active_limit_mb"])
        self.assertIn("organizer", status["active_workers"])

    def test_model_loading_and_unloading(self):
        # Load vision worker (4100 MB)
        loaded = MODEL_MGR.load_worker("vision")
        self.assertTrue(loaded)
        self.assertTrue(MODEL_MGR.is_loaded("vision"))

        # Unload vision worker
        unloaded = MODEL_MGR.unload_worker("vision")
        self.assertTrue(unloaded)
        self.assertFalse(MODEL_MGR.is_loaded("vision"))

    def test_automatic_model_swapping_under_budget(self):
        # Simulate a constrained deployment budget independently of host hardware.
        original_budget = MODEL_MGR.vram_budget_mb
        try:
            MODEL_MGR.vram_budget_mb = 7168

            MODEL_MGR.load_worker("vision")
            self.assertTrue(MODEL_MGR.is_loaded("vision"))

            # organizer 1200 + vision 4100 + document 3600 = 8900
            # The manager should evict an idle specialist before loading document.
            loaded_doc = MODEL_MGR.load_worker("document")

            self.assertTrue(loaded_doc)
            self.assertTrue(MODEL_MGR.is_loaded("document"))
            self.assertFalse(
                MODEL_MGR.is_loaded("vision"),
                "Vision worker should have been evicted to satisfy simulated memory budget",
            )
            self.assertLessEqual(
                MODEL_MGR.get_current_vram_used(),
                MODEL_MGR.vram_budget_mb,
            )
        finally:
            MODEL_MGR.vram_budget_mb = original_budget


    def test_worker_reuse_optimization(self):
        # Consecutive calls to the same worker should increment reuse count without reloading
        initial_reuses = MODEL_MGR.metrics["reuses_count"]
        MODEL_MGR.load_worker("coding")
        MODEL_MGR.load_worker("coding")  # Second load is a reuse
        self.assertGreater(MODEL_MGR.metrics["reuses_count"], initial_reuses)


if __name__ == "__main__":
    unittest.main()

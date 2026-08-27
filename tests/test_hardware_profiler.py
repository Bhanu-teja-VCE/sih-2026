"""
tests/test_hardware_profiler.py
Evaluation tests for the Hardware Resource Guard and Telemetry Profiler.
Verifies memory detection, CPU metrics, and execution safety checks.
"""

import unittest
from harness.hardware_profiler import HardwareResourceGuard


class TestHardwareProfiler(unittest.TestCase):

    def setUp(self):
        self.guard = HardwareResourceGuard()

    def test_get_telemetry_structure(self):
        telemetry = self.guard.get_telemetry()
        self.assertGreater(telemetry.ram_total_gb, 0.0)
        self.assertGreaterEqual(telemetry.cpu_percent, 0.0)
        self.assertIn("STATION", telemetry.hardware_grade)

    def test_is_execution_safe(self):
        # The laptop has plenty of free memory (> 500MB)
        is_safe = self.guard.is_execution_safe(min_required_free_mb=100.0)
        self.assertTrue(is_safe)


if __name__ == "__main__":
    unittest.main()

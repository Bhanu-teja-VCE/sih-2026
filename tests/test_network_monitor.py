"""
tests/test_network_monitor.py
Evaluation tests for the Sovereign Air-Gap Network Monitor.
Verifies real-time socket inspection, IP classification, and audit log generation.
"""

import unittest
from harness.network_monitor import NetworkAirGapMonitor


class TestNetworkAirGapMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = NetworkAirGapMonitor()

    def test_ip_classification_loopback_and_lan(self):
        self.assertTrue(self.monitor.is_ip_allowed("127.0.0.1"))
        self.assertTrue(self.monitor.is_ip_allowed("192.168.1.100"))
        self.assertTrue(self.monitor.is_ip_allowed("10.0.0.50"))
        self.assertTrue(self.monitor.is_ip_allowed("172.20.10.4"))

    def test_ip_classification_public_wan(self):
        # Public IP addresses (e.g. OpenAI / Google / AWS public endpoints)
        self.assertFalse(self.monitor.is_ip_allowed("8.8.8.8"))
        self.assertFalse(self.monitor.is_ip_allowed("104.18.20.100"))
        self.assertFalse(self.monitor.is_ip_allowed("142.250.190.46"))

    def test_scan_sockets_structure(self):
        status = self.monitor.scan_sockets()

        self.assertIn("is_airgapped", status)
        self.assertIn("sovereign_status", status)
        self.assertIn("external_egress_violations_count", status)
        self.assertIsInstance(status["scan_duration_ms"], (int, float))

    def test_generate_audit_log(self):
        log = self.monitor.generate_audit_log()

        self.assertIn("MANGALORE REFINERY", log)
        self.assertIn("AIR-GAP AUDIT CERTIFICATE", log)
        self.assertIn("Outbound WAN Packets", log)


if __name__ == "__main__":
    unittest.main()

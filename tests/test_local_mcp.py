"""
tests/test_local_mcp.py
Evaluation tests for the Local Model Context Protocol (MCP) Engine.
Verifies tool discovery, schema integrity, and in-memory execution.
"""

import unittest
from harness.local_mcp import LocalMCPEngine, MCPToolCall


class TestLocalMCP(unittest.TestCase):

    def setUp(self):
        self.engine = LocalMCPEngine()

    def test_list_default_tools(self):
        tools = self.engine.list_tools()
        self.assertGreaterEqual(len(tools), 3)
        tool_names = [t.name for t in tools]
        self.assertIn("asme_b31_3_calculator", tool_names)
        self.assertIn("sovereign_sop_lookup", tool_names)
        self.assertIn("parse_ultrasonic_excel", tool_names)

    def test_call_asme_calculator_tool(self):
        call = MCPToolCall(
            tool_name="asme_b31_3_calculator",
            arguments={
                "design_pressure_mpa": 4.0,
                "outer_diameter_mm": 219.1,
                "allowable_stress_mpa": 137.0,
                "measured_thickness_mm": 7.48,
                "annual_corrosion_rate_mm": 0.25
            }
        )
        res = self.engine.call_tool(call)
        self.assertFalse(res.is_error)
        self.assertEqual(res.content["status"], "APPROVED_SAFE")
        self.assertGreater(res.content["remaining_life_years"], 4.0)

    def test_call_sop_lookup_tool(self):
        call = MCPToolCall(
            tool_name="sovereign_sop_lookup",
            arguments={"query": "corrosion allowance", "top_k": 1}
        )
        res = self.engine.call_tool(call)
        self.assertFalse(res.is_error)
        self.assertGreaterEqual(len(res.content), 1)

    def test_unknown_tool_call(self):
        call = MCPToolCall(tool_name="non_existent_tool", arguments={})
        res = self.engine.call_tool(call)
        self.assertTrue(res.is_error)


if __name__ == "__main__":
    unittest.main()

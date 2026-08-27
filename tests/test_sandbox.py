"""
tests/test_sandbox.py
Evaluation tests for the Sandboxed Execution Runner and Circuit Breaker.
Verifies arithmetic correctness, timeout isolation, AST security blocking (bare names + attributes), and error trapping.
"""

import unittest
from harness.sandbox import CalculationSandbox


class TestCalculationSandbox(unittest.TestCase):

    def setUp(self):
        self.sandbox = CalculationSandbox(default_timeout_seconds=2.0)

    def test_simple_arithmetic_execution(self):
        code = "print(40 + 2)"
        res = self.sandbox.execute(code)

        self.assertTrue(res.success)
        self.assertEqual(res.output, 42)
        self.assertIsNone(res.error)

    def test_asme_b31_3_calculation(self):
        code = self.sandbox.generate_asme_b31_3_script(
            design_pressure_mpa=4.0,
            outer_diameter_mm=219.1,
            allowable_stress_mpa=137.0,
            joint_efficiency=1.0,
            y_coefficient=0.4,
            corrosion_allowance_mm=3.0,
            measured_thickness_mm=7.5,
            annual_corrosion_rate_mm=0.25,
        )
        res = self.sandbox.execute(code)

        self.assertTrue(res.success)
        self.assertIsInstance(res.output, dict)
        self.assertIn("ASME", res.output["standard"])
        self.assertEqual(res.output["status"], "APPROVED_SAFE")
        self.assertGreater(res.output["remaining_life_years"], 0)

    def test_ast_security_blocks_dynamic_execution_tunneling(self):
        # 1. Bare exec() call
        exec_code = 'exec("import socket\\ns = socket.socket()")'
        res = self.sandbox.execute(exec_code)
        self.assertFalse(res.success)
        self.assertIn("Security Violation", res.error)

        # 2. Bare eval() call
        eval_code = 'eval("1 + 1")'
        res2 = self.sandbox.execute(eval_code)
        self.assertFalse(res2.success)
        self.assertIn("Security Violation", res2.error)

        # 3. Bare __import__() call
        imp_code = '__import__("os").system("dir")'
        res3 = self.sandbox.execute(imp_code)
        self.assertFalse(res3.success)
        self.assertIn("Security Violation", res3.error)

    def test_ast_security_blocks_file_io_and_system_calls(self):
        # 4. Bare open() file read call
        open_code = 'content = open("secret.txt").read()'
        res4 = self.sandbox.execute(open_code)
        self.assertFalse(res4.success)
        self.assertIn("Security Violation", res4.error)

        # 5. from os import system; system()
        from_sys_code = 'from os import system\nsystem("dir")'
        res5 = self.sandbox.execute(from_sys_code)
        self.assertFalse(res5.success)
        self.assertIn("Security Violation", res5.error)

        # 6. import shutil; shutil.rmtree()
        shutil_code = 'import shutil\nshutil.rmtree("temp")'
        res6 = self.sandbox.execute(shutil_code)
        self.assertFalse(res6.success)
        self.assertIn("Security Violation", res6.error)

        # 7. import importlib
        importlib_code = 'import importlib\nimportlib.import_module("socket")'
        res7 = self.sandbox.execute(importlib_code)
        self.assertFalse(res7.success)
        self.assertIn("Security Violation", res7.error)

    def test_syntax_error_capture(self):
        bad_code = "print('Unclosed string"
        res = self.sandbox.execute(bad_code)

        self.assertFalse(res.success)
        self.assertIsNone(res.output)
        self.assertIn("SyntaxError", res.error)

    def test_runtime_exception_capture(self):
        div_zero_code = "x = 10 / 0"
        res = self.sandbox.execute(div_zero_code)

        self.assertFalse(res.success)
        self.assertIsNone(res.output)
        self.assertIn("ZeroDivisionError", res.error)

    def test_infinite_loop_timeout_protection(self):
        loop_code = "while True: pass"
        res = self.sandbox.execute(loop_code, timeout=0.5)

        self.assertFalse(res.success)
        self.assertIsNone(res.output)
        self.assertIn("timed out", res.error.lower())


if __name__ == "__main__":
    unittest.main()

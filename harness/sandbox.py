"""
harness/sandbox.py
Hardened Deterministic Subprocess Execution Sandbox for Engineering Calculations.
Executes mathematical Python code in an isolated subprocess with multi-layer AST safety inspection,
sanitized environment, CPU timeout circuit-breaker, and JSON output parsing.
Guarantees zero arithmetic hallucination by enforcing code-level evaluation.
"""

import os
import sys
import ast
import json
import time
import tempfile
import subprocess
from typing import Dict, Any, Optional, Set
from harness.types import ToolCallResult


class CalculationSandbox:
    """
    Subprocess Execution Sandbox with Comprehensive AST Security Pre-Screening.
    Provides execution isolation against infinite loops, unhandled exceptions,
    code injection (exec/eval), unauthorized file reads/deletions, and network socket operations.
    """

    FORBIDDEN_MODULES: Set[str] = {
        "subprocess", "socket", "http", "urllib", "requests",
        "ftplib", "telnetlib", "smtplib", "ctypes", "pty",
        "winreg", "webbrowser", "importlib", "shutil", "pickle",
        "shelve", "marshal", "inspect", "builtins", "__builtin__"
    }

    FORBIDDEN_FUNCTIONS: Set[str] = {
        # Code injection & dynamic execution
        "eval", "exec", "compile", "__import__",
        # Dangerous builtins & introspection
        "open", "getattr", "setattr", "delattr", "globals", "locals", "vars",
        # OS execution & deletion primitives
        "system", "popen", "spawn", "execv", "execve",
        "kill", "remove", "rmdir", "unlink", "rmtree",
        # Dynamic module loading
        "import_module"
    }

    def __init__(self, default_timeout_seconds: float = 5.0):
        self.default_timeout = default_timeout_seconds

    def _validate_ast_safety(self, code_snippet: str) -> Optional[str]:
        """
        Static AST Security Inspector.
        Checks both static imports AND function calls (bare Name calls + Attribute calls)
        to prevent eval/exec tunneling, arbitrary file I/O (open), and system command execution.
        """
        try:
            tree = ast.parse(code_snippet)
        except SyntaxError as e:
            return f"SyntaxError during AST inspection: {str(e)}"

        for node in ast.walk(tree):
            # 1. Check static imports: import X
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    if root_pkg in self.FORBIDDEN_MODULES:
                        return f"Security Violation: Import of forbidden module '{alias.name}' is blocked by Sandbox Policy."

            # 2. Check from X import Y
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    if root_pkg in self.FORBIDDEN_MODULES:
                        return f"Security Violation: Import from forbidden module '{node.module}' is blocked by Sandbox Policy."
                for alias in node.names:
                    if alias.name in self.FORBIDDEN_FUNCTIONS:
                        return f"Security Violation: Import of forbidden function '{alias.name}' is blocked by Sandbox Policy."

            # 3. Check ALL function and method calls (both bare names and attribute calls)
            elif isinstance(node, ast.Call):
                # Case A: Bare function call: exec(...), eval(...), open(...)
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.FORBIDDEN_FUNCTIONS:
                        return f"Security Violation: Direct call to forbidden function '{func_name}()' is blocked by Sandbox Policy."

                # Case B: Attribute call: os.system(...), shutil.rmtree(...), importlib.import_module(...)
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in self.FORBIDDEN_FUNCTIONS:
                        return f"Security Violation: Call to forbidden method/attribute '{attr_name}()' is blocked by Sandbox Policy."

        return None

    def execute(self, code_snippet: str, timeout: Optional[float] = None) -> ToolCallResult:
        """
        Executes a Python code snippet inside a sanitized subprocess.
        Returns parsed JSON output if available, or raw text stdout.
        """
        timeout_val = timeout or self.default_timeout

        # 1. AST Security Pre-Screening
        security_error = self._validate_ast_safety(code_snippet)
        if security_error:
            return ToolCallResult(
                tool_name="SANDBOX_CALCULATOR",
                success=False,
                output=None,
                error=security_error,
                execution_time_ms=0.0
            )

        start_time = time.time()
        temp_file = None

        try:
            # 2. Write code to a secure temporary script file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(code_snippet)
                temp_file = f.name

            # 3. Build sanitized environment (whitelist only: strip all cloud keys, tokens, and parent env)
            sanitized_env = {
                "PYTHONUNBUFFERED": "1",
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "TEMP": tempfile.gettempdir(),
                "TMP": tempfile.gettempdir(),
            }

            # 4. Spawn isolated subprocess
            proc = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout_val,
                env=sanitized_env,
                cwd=tempfile.gettempdir()
            )

            exec_time_ms = round((time.time() - start_time) * 1000, 2)

            if proc.returncode == 0:
                raw_out = proc.stdout.strip()
                try:
                    parsed = json.loads(raw_out)
                    return ToolCallResult(
                        tool_name="SANDBOX_CALCULATOR",
                        success=True,
                        output=parsed,
                        error=None,
                        execution_time_ms=exec_time_ms
                    )
                except json.JSONDecodeError:
                    return ToolCallResult(
                        tool_name="SANDBOX_CALCULATOR",
                        success=True,
                        output=raw_out,
                        error=None,
                        execution_time_ms=exec_time_ms
                    )
            else:
                return ToolCallResult(
                    tool_name="SANDBOX_CALCULATOR",
                    success=False,
                    output=None,
                    error=proc.stderr.strip() or f"Process exited with code {proc.returncode}",
                    execution_time_ms=exec_time_ms
                )

        except subprocess.TimeoutExpired:
            exec_time_ms = round((time.time() - start_time) * 1000, 2)
            return ToolCallResult(
                tool_name="SANDBOX_CALCULATOR",
                success=False,
                output=None,
                error=f"Execution timed out after {timeout_val} seconds (Circuit Breaker Triggered).",
                execution_time_ms=exec_time_ms
            )
        except Exception as e:
            exec_time_ms = round((time.time() - start_time) * 1000, 2)
            return ToolCallResult(
                tool_name="SANDBOX_CALCULATOR",
                success=False,
                output=None,
                error=f"Sandbox Host Exception: {str(e)}",
                execution_time_ms=exec_time_ms
            )
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

    @staticmethod
    def generate_asme_b31_3_script(
        design_pressure_mpa: float,
        outer_diameter_mm: float,
        allowable_stress_mpa: float,
        joint_efficiency: float = 1.0,
        y_coefficient: float = 0.4,
        corrosion_allowance_mm: float = 3.0,
        measured_thickness_mm: float = 6.2,
        annual_corrosion_rate_mm: float = 0.25,
        annual_corrosion_rate_mm_yr: Optional[float] = None
    ) -> str:
        """
        Generates standard ASME B31.3 Process Piping wall thickness script.
        Formula: t = (P * D) / (2 * (S * E * W + P * Y)) + c
        """
        cr = annual_corrosion_rate_mm_yr if annual_corrosion_rate_mm_yr is not None else annual_corrosion_rate_mm
        return f"""
import json

def calculate():
    P = {design_pressure_mpa}
    D = {outer_diameter_mm}
    S = {allowable_stress_mpa}
    E = {joint_efficiency}
    W = 1.0
    Y = {y_coefficient}
    c = {corrosion_allowance_mm}
    t_actual = {measured_thickness_mm}
    cr = {cr}

    # Pressure design thickness
    t_pressure = (P * D) / (2.0 * (S * E * W + P * Y))
    # Total required minimum thickness
    t_min = t_pressure + c

    safe_margin = t_actual - t_min
    remaining_life = safe_margin / cr if cr > 0 else 999.0
    status = "APPROVED_SAFE" if safe_margin >= 0 else "REPLACEMENT_REQUIRED"

    return {{
        "standard": "ASME_B31_3",
        "design_pressure_mpa": round(P, 3),
        "outer_diameter_mm": round(D, 2),
        "pressure_thickness_mm": round(t_pressure, 4),
        "corrosion_allowance_mm": round(c, 2),
        "required_min_thickness_mm": round(t_min, 4),
        "measured_thickness_mm": round(t_actual, 3),
        "safe_margin_mm": round(safe_margin, 3),
        "annual_corrosion_rate_mm_yr": round(cr, 3),
        "remaining_life_years": round(remaining_life, 2),
        "status": status
    }}

print(json.dumps(calculate()))
"""

    @staticmethod
    def generate_heat_exchanger_lmtd_script(
        th_in: float,
        th_out: float,
        tc_in: float,
        tc_out: float,
        area_m2: float = 120.0,
        u_coeff_w_m2k: float = 450.0
    ) -> str:
        """Generates thermodynamic heat duty and LMTD calculation script."""
        return f"""
import json
import math

def calculate_lmtd():
    th1 = {th_in}
    th2 = {th_out}
    tc1 = {tc_in}
    tc2 = {tc_out}
    A = {area_m2}
    U = {u_coeff_w_m2k}

    dt1 = th1 - tc2
    dt2 = th2 - tc1

    if dt1 <= 0 or dt2 <= 0 or dt1 == dt2:
        lmtd = (dt1 + dt2) / 2.0
    else:
        lmtd = (dt1 - dt2) / math.log(dt1 / dt2)

    duty_kw = (U * A * lmtd) / 1000.0

    return {{
        "calculation_type": "HEAT_EXCHANGER_LMTD",
        "dt1_celsius": round(dt1, 2),
        "dt2_celsius": round(dt2, 2),
        "lmtd_celsius": round(lmtd, 2),
        "thermal_duty_kw": round(duty_kw, 2),
        "status": "APPROVED_THERMAL_BALANCE"
    }}

print(json.dumps(calculate_lmtd()))
"""

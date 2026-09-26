"""
Verifier — runs tests from an explicit allowlist of safe commands.
Never executes arbitrary user input.
"""
from __future__ import annotations
import os
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional


# ─── Command Allowlist ────────────────────────────────────────────────────────
# Only these exact command patterns may be executed.
# No user-provided arguments are ever passed to the shell.

ALLOWED_COMMANDS = [
    ["python", "-m", "pytest"],
    ["python", "-m", "pytest", "-v"],
    ["python", "-m", "pytest", "--tb=short"],
    ["python", "-m", "pytest", "-v", "--tb=short"],
    ["python", "-m", "pytest", "tests/", "-v"],
    ["python", "-m", "pytest", "tests/", "--tb=short"],
    ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
]

# Maximum allowed test output (characters)
MAX_OUTPUT_CHARS = 8000


@dataclass
class VerificationResult:
    command: str
    status: str         # 'passed' | 'failed' | 'error'
    duration_ms: int
    output: str
    passed: bool


_DEMO_VERIFICATION_OUTPUT = """\
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-8.3.3
rootdir: /sample_project
collected 17 items

tests/test_auth.py::TestTokenAuth::test_valid_token_returns_user PASSED   [  5%]
tests/test_auth.py::TestTokenAuth::test_invalid_token_raises_auth_error PASSED [ 11%]
tests/test_auth.py::TestTokenAuth::test_inactive_user_raises_auth_error PASSED [ 17%]
tests/test_auth.py::TestRequireRole::test_matching_role_passes PASSED     [ 23%]
tests/test_auth.py::TestRequireRole::test_non_matching_role_raises PASSED [ 29%]
tests/test_auth.py::TestRequireRole::test_multiple_acceptable_roles PASSED [ 35%]
tests/test_orders.py::TestCreateOrder::test_creates_pending_order PASSED  [ 41%]
tests/test_orders.py::TestCreateOrder::test_raises_on_empty_items PASSED  [ 47%]
tests/test_orders.py::TestCreateOrder::test_raises_on_negative_quantity PASSED [ 52%]
tests/test_orders.py::TestCreateOrder::test_raises_on_negative_price PASSED [ 58%]
tests/test_orders.py::TestUpdateOrder::test_customer_can_update_own_pending_order PASSED [ 64%]
tests/test_orders.py::TestUpdateOrder::test_customer_cannot_update_others_order PASSED [ 70%]
tests/test_orders.py::TestUpdateOrder::test_cannot_update_confirmed_order PASSED [ 76%]
tests/test_orders.py::TestUpdateOrder::test_admin_can_apply_discount PASSED [ 82%]
tests/test_orders.py::TestUpdateOrder::test_customer_cannot_apply_discount PASSED [ 88%]
tests/test_orders.py::TestCancelOrder::test_can_cancel_pending_order PASSED [ 94%]
tests/test_orders.py::TestCancelOrder::test_cannot_cancel_shipped_order PASSED [100%]

============================== 17 passed in 0.08s ==============================
"""


def verify(
    project_root: str,
    generated_test_path: Optional[str] = None,
) -> VerificationResult:
    """
    Run the project test suite and return structured results.
    Uses only allowlisted commands. No user input reaches subprocess.

    On serverless (no project directory / no pytest), returns an honest
    'skipped' result instead of fabricated pass output.
    """
    command = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
    command_str = ' '.join(command)

    if not os.path.isdir(project_root):
        return VerificationResult(
            command=command_str,
            status='skipped',
            duration_ms=0,
            output=(
                "Verification skipped: project directory is not available in this "
                "runtime (serverless). Risk/test analysis above is still from live AI."
            ),
            passed=False,
        )

    if command not in ALLOWED_COMMANDS:
        return VerificationResult(
            command=command_str,
            status='error',
            duration_ms=0,
            output="Command not in allowlist",
            passed=False,
        )

    start = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        output = (result.stdout + result.stderr)[:MAX_OUTPUT_CHARS]

        if result.returncode != 0 and (
            "No module named pytest" in output or "pytest: not found" in output
        ):
            return VerificationResult(
                command=command_str,
                status='skipped',
                duration_ms=duration_ms,
                output=(
                    "Verification skipped: pytest is not installed in this runtime.\n"
                    + output
                ),
                passed=False,
            )

        passed = result.returncode == 0
        return VerificationResult(
            command=command_str,
            status='passed' if passed else 'failed',
            duration_ms=duration_ms,
            output=output,
            passed=passed,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return VerificationResult(
            command=command_str,
            status='error',
            duration_ms=duration_ms,
            output='Test run timed out after 60 seconds',
            passed=False,
        )
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return VerificationResult(
            command=command_str,
            status='skipped',
            duration_ms=duration_ms,
            output=f"Verification skipped in this runtime: {e}",
            passed=False,
        )


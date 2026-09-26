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


def verify(
    project_root: str,
    generated_test_path: Optional[str] = None,
) -> VerificationResult:
    """
    Run the project test suite and return structured results.
    Uses only allowlisted commands. No user input reaches subprocess.
    """
    command = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
    command_str = ' '.join(command)

    # Security check: project_root must be an existing directory
    if not os.path.isdir(project_root):
        return VerificationResult(
            command=command_str,
            status='error',
            duration_ms=0,
            output=f"Project directory not found: {project_root}",
            passed=False,
        )

    # Ensure the command is in our allowlist
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
            # Never use shell=True
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        output = (result.stdout + result.stderr)[:MAX_OUTPUT_CHARS]

        passed = result.returncode == 0
        status = 'passed' if passed else 'failed'

        return VerificationResult(
            command=command_str,
            status=status,
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
            status='error',
            duration_ms=duration_ms,
            output=f"Verification error: {str(e)}",
            passed=False,
        )

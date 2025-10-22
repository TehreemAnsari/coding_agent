import json
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Tuple, Set, Optional
from datetime import datetime


class CodeRunner:
    """
    Safe code execution engine for generated Python solutions.
    Provides configurable safety checks and isolated execution.
    """

    DEFAULT_ALLOWED_IMPORTS = {
        "math", "random", "itertools", "functools", "collections",
        "heapq", "bisect", "array", "queue", "string", "re",
        "datetime", "time", "decimal", "fractions", "statistics",
        "json", "copy", "typing"
    }

    DEFAULT_DANGEROUS_PATTERNS = [
        "import os", "from os", "import sys", "from sys",
        "import subprocess", "from subprocess",
        "import socket", "from socket",
        "import shutil", "from shutil",
        "eval(", "exec(", "compile(", "__import__",
        "open(", "file(", "input(", "raw_input(",
        "globals(", "locals(", "vars(",
        "getattr", "setattr", "delattr",
        "breakpoint(", "help(", "dir("
    ]

    def __init__(self, allowed_imports: Optional[Set[str]] = None,
                 dangerous_patterns: Optional[List[str]] = None,
                 default_timeout: int = 6,
                 runs_dir: Optional[str] = None):
        """Initialize CodeRunner with safety and execution settings."""
        self.allowed_imports = allowed_imports or self.DEFAULT_ALLOWED_IMPORTS
        self.dangerous_patterns = dangerous_patterns or self.DEFAULT_DANGEROUS_PATTERNS
        self.default_timeout = default_timeout

        # Directory for run logs
        self.runs_dir = runs_dir or os.path.join(os.path.dirname(__file__), "..", "runs")
        os.makedirs(self.runs_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # SAFETY CHECKS
    # -------------------------------------------------------------------------
    def _validate_code_safety(self, code: str) -> None:
        """Block unsafe imports and patterns."""
        code_lower = code.lower()
        for pattern in self.dangerous_patterns:
            if pattern.lower() in code_lower:
                raise RuntimeError(f"Blocked potentially unsafe code pattern: {pattern}")

        for line in code.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                parts = stripped.split()
                if len(parts) >= 2:
                    module = parts[1] if stripped.startswith("from") else parts[1].split(".")[0]
                    if module not in self.allowed_imports and module != "solve":
                        raise RuntimeError(
                            f"Import '{module}' not allowed. Only standard library modules are permitted."
                        )

    # -------------------------------------------------------------------------
    # FILE CREATION
    # -------------------------------------------------------------------------
    def _make_solution_file(self, generated_code: str) -> str:
        """Write generated code to an isolated temporary file with safe wrapper."""
        self._validate_code_safety(generated_code)

        # Escape braces to avoid f-string parsing
        wrapper = f"""
import json
import sys

{generated_code}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    try:
        payload = json.loads(args.input)
        if isinstance(payload, dict):
            fargs = payload.get("args", [])
            fkwargs = payload.get("kwargs", {{}}
)
        else:
            fargs, fkwargs = payload, {{}}

        if 'solve' not in globals():
            print(json.dumps({{"error": "No 'solve' function found in generated code"}}))
            sys.exit(1)

        fn = globals()['solve']

        # Flexible call strategy
        try:
            result = fn(*fargs, **fkwargs)
        except TypeError:
            try:
                result = fn(fargs, **fkwargs)
            except TypeError:
                if isinstance(fargs, list) and len(fargs) == 1:
                    try:
                        result = fn(*fargs[0], **fkwargs)
                    except Exception:
                        result = fn(fargs[0], **fkwargs)
                else:
                    print(json.dumps({{"error": "Could not match function signature"}}))
                    sys.exit(1)

        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({{"error": str(e)}}))
        sys.exit(1)
"""
        tmpdir = tempfile.mkdtemp(prefix="code_solver_")
        path = os.path.join(tmpdir, "solution.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(wrapper)
        return path

    # -------------------------------------------------------------------------
    # EXECUTION
    # -------------------------------------------------------------------------
    def _exec_solution(self, solution_path: str, input_payload: Dict[str, Any], timeout: Optional[int] = None
                       ) -> Tuple[bool, str, str, int]:
        """Safely execute generated code with timeout and capture output."""
        timeout = timeout or self.default_timeout
        cmd = ["python", solution_path, "--input", json.dumps(input_payload)]
        start = time.time()
        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            runtime_ms = int((time.time() - start) * 1000)
            return True, completed.stdout.strip(), completed.stderr.strip(), runtime_ms
        except subprocess.TimeoutExpired:
            return False, "", f"Timeout after {timeout}s", timeout * 1000
        except Exception as e:
            return False, "", str(e), int((time.time() - start) * 1000)

    # -------------------------------------------------------------------------
    # MAIN TEST RUN
    # -------------------------------------------------------------------------
    def run_tests(self, problem_text: str, generated_code: str,
                  test_cases: List[Tuple[List[Any], Any]],
                  llm_trajectory=None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Run multiple test cases and return structured results."""
        results = []
        passed = 0
        total = len(test_cases)
        exec_timeout = timeout or self.default_timeout

        try:
            solution_path = self._make_solution_file(generated_code)
        except RuntimeError as e:
            return {
                "run_id": str(int(time.time() * 1000)),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "problem_text": problem_text,
                "solution_code": generated_code,
                "test_cases": [],
                "score": 0.0,
                "error": str(e),
                "llm_trajectory": llm_trajectory or [],
            }

        for inp, expected in test_cases:
            payload = {"args": inp if isinstance(inp, list) else [inp]}
            ok, stdout, stderr, runtime_ms = self._exec_solution(solution_path, payload, exec_timeout)
            output, error, passed_case = None, None, False

            if not ok:
                error = stderr or "Execution failed"
            else:
                try:
                    parsed = json.loads(stdout)
                    if isinstance(parsed, dict) and "error" in parsed:
                        error = parsed["error"]
                    else:
                        output = parsed
                except Exception:
                    output = stdout

            if error is None:
                try:
                    passed_case = (output == expected) or (
                        json.dumps(output, sort_keys=True) == json.dumps(expected, sort_keys=True)
                    )
                except Exception:
                    passed_case = (output == expected)
                if passed_case:
                    passed += 1

            results.append({
                "input": json.dumps(inp),
                "expected_output": json.dumps(expected),
                "output": json.dumps(output) if output is not None else None,
                "passed": passed_case,
                "error": error,
                "runtime_ms": runtime_ms,
            })

        score = passed / total if total else 0.0

        return {
            "run_id": str(int(time.time() * 1000)),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "problem_text": problem_text,
            "solution_code": generated_code,
            "test_cases": results,
            "score": score,
            "error": None,
            "llm_trajectory": llm_trajectory or [],
        }


# -------------------------------------------------------------------------
# Backward-compatible function
# -------------------------------------------------------------------------
def run(problem_text: str, generated_code: str,
        test_cases: List[Tuple[List[Any], Any]], llm_trajectory=None):
    """Convenience wrapper for backwards compatibility."""
    runner = CodeRunner()
    return runner.run_tests(problem_text, generated_code, test_cases, llm_trajectory)

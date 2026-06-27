"""
Multi-Language Code Execution Engine
Supports: Python, Java, C++, JavaScript

Execution strategy (tiered):
  1. Docker sandbox (if available) — fully isolated
  2. Process-isolated subprocess fallback — timeout + env scrubbing

Returns rich per-test-case results.
"""

import subprocess
import time
import sys
import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional


SUPPORTED_LANGUAGES = ["python", "java", "cpp", "javascript", "typescript"]

# Timeouts and limits
TEST_TIMEOUT_SECS = 10
COMPILE_TIMEOUT_SECS = 30
MEMORY_LIMIT_KB = 131072  # 128 MB


class CodeExecutor:
    """
    Secure, multi-language code execution engine.
    Docker-first, subprocess fallback.
    """

    SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGES

    @staticmethod
    def execute(
        code: str,
        language: str,
        public_test_cases: List[Dict],
        hidden_test_cases: Optional[List[Dict]] = None,
        timeout: int = TEST_TIMEOUT_SECS,
        is_final: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute code against test cases.
        Returns: {
            status, runtime_ms, memory_kb, output,
            public_results, hidden_passed, hidden_total, all_passed
        }
        """
        lang = language.lower().strip()
        hidden_test_cases = hidden_test_cases or []

        if lang not in SUPPORTED_LANGUAGES:
            return {
                "status": "Unsupported Language",
                "output": f"Language '{language}' is not supported. Choose: {', '.join(SUPPORTED_LANGUAGES)}",
                "public_results": [],
                "hidden_passed": 0,
                "hidden_total": len(hidden_test_cases),
                "all_passed": False,
                "runtime_ms": 0,
                "memory_kb": 0,
            }

        # Run against public TCs (full detail shown to user)
        public_results = CodeExecutor._run_test_cases(
            code, lang, public_test_cases, timeout, expose_io=True
        )

        # Run against hidden TCs (only pass/fail count returned)
        hidden_results = []
        if is_final and hidden_test_cases:
            hidden_results = CodeExecutor._run_test_cases(
                code, lang, hidden_test_cases, timeout, expose_io=False
            )

        # Aggregate
        all_results = public_results + hidden_results
        passed = sum(1 for r in all_results if r["passed"])
        total = len(all_results)

        hidden_passed = sum(1 for r in hidden_results if r["passed"])

        # Derive overall status
        if total == 0:
            overall_status = "Accepted"
        elif all(r["passed"] for r in all_results):
            overall_status = "Accepted"
        elif any(r.get("error_type") == "TLE" for r in all_results):
            overall_status = "Time Limit Exceeded"
        elif any(r.get("error_type") == "MLE" for r in all_results):
            overall_status = "Memory Limit Exceeded"
        elif any(r.get("error_type") == "RuntimeError" for r in all_results):
            overall_status = "Runtime Error"
        elif any(r.get("error_type") == "CompilationError" for r in all_results):
            overall_status = "Compilation Error"
        else:
            overall_status = "Wrong Answer"

        avg_runtime = (
            int(sum(r.get("runtime_ms", 0) for r in all_results) / len(all_results))
            if all_results else 0
        )
        max_memory = max((r.get("memory_kb", 0) for r in all_results), default=0)

        # Format public results for frontend
        formatted_public = [
            {
                "test_number": i + 1,
                "passed": r["passed"],
                "runtime_ms": r.get("runtime_ms"),
                "memory_kb": r.get("memory_kb"),
                "input": r.get("input"),
                "expected": r.get("expected"),
                "actual": r.get("actual"),
                "error": r.get("error"),
            }
            for i, r in enumerate(public_results)
        ]

        return {
            "status": overall_status,
            "runtime_ms": avg_runtime,
            "memory_kb": max_memory,
            "output": _build_output_summary(public_results),
            "public_results": formatted_public,
            "hidden_passed": hidden_passed,
            "hidden_total": len(hidden_test_cases),
            "all_passed": overall_status == "Accepted",
        }

    @staticmethod
    def _run_test_cases(
        code: str,
        lang: str,
        test_cases: List[Dict],
        timeout: int,
        expose_io: bool,
    ) -> List[Dict]:
        """Run code against a list of test cases, returning per-case results."""
        if not test_cases:
            return []

        # Try Docker first, fall back to subprocess
        use_docker = _docker_available()

        results = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Compile once for compiled languages
            compile_error = None
            exec_path = None

            if lang == "java":
                src_path = os.path.join(tmp_dir, "Solution.java")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(code)
                compile_error = _compile_java(src_path, tmp_dir)
                if not compile_error:
                    exec_path = tmp_dir  # compiled .class files here

            elif lang == "cpp":
                src_path = os.path.join(tmp_dir, "solution.cpp")
                out_path = os.path.join(tmp_dir, "solution")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(code)
                compile_error = _compile_cpp(src_path, out_path)
                if not compile_error:
                    exec_path = out_path

            elif lang == "python":
                src_path = os.path.join(tmp_dir, "solution.py")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(code)
                exec_path = src_path

            elif lang == "javascript":
                src_path = os.path.join(tmp_dir, "solution.js")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(code)
                exec_path = src_path

            elif lang == "typescript":
                src_path = os.path.join(tmp_dir, "solution.ts")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(code)
                js_path = os.path.join(tmp_dir, "solution.js")
                compile_error = _compile_typescript(src_path, js_path)
                if not compile_error:
                    exec_path = js_path

            if compile_error:
                # All test cases fail with compilation error
                for tc in test_cases:
                    results.append({
                        "passed": False,
                        "error_type": "CompilationError",
                        "error": compile_error,
                        "runtime_ms": 0,
                        "memory_kb": 0,
                        "input": tc.get("input") if expose_io else None,
                        "expected": tc.get("expected") if expose_io else None,
                        "actual": None,
                    })
                return results

            for i, tc in enumerate(test_cases):
                tc_input = tc.get("input", "")
                tc_expected = tc.get("expected", "").strip()

                start = time.perf_counter()
                try:
                    if use_docker and lang == "python":
                        result = _run_docker_python(exec_path, tc_input, timeout)
                    elif lang == "python":
                        result = _run_subprocess([sys.executable, exec_path], tc_input, timeout)
                    elif lang == "java":
                        result = _run_subprocess(
                            ["java", "-cp", exec_path, "Solution"],
                            tc_input, timeout
                        )
                    elif lang == "cpp":
                        result = _run_subprocess([exec_path], tc_input, timeout)
                    elif lang == "javascript":
                        result = _run_subprocess(["node", exec_path], tc_input, timeout)
                    elif lang == "typescript":
                        result = _run_subprocess(["node", exec_path], tc_input, timeout)
                    else:
                        result = {"returncode": 1, "stdout": "", "stderr": "Unknown language", "timed_out": False}

                    elapsed_ms = int((time.perf_counter() - start) * 1000)

                    if result.get("timed_out"):
                        results.append({
                            "passed": False,
                            "error_type": "TLE",
                            "error": f"Time Limit Exceeded (>{timeout}s)",
                            "runtime_ms": timeout * 1000,
                            "memory_kb": 0,
                            "input": tc_input if expose_io else None,
                            "expected": tc_expected if expose_io else None,
                            "actual": None,
                        })
                        continue

                    if result["returncode"] != 0:
                        err_msg = (result.get("stderr") or result.get("stdout") or "Runtime Error").strip()
                        results.append({
                            "passed": False,
                            "error_type": "RuntimeError",
                            "error": err_msg[:500],
                            "runtime_ms": elapsed_ms,
                            "memory_kb": 0,
                            "input": tc_input if expose_io else None,
                            "expected": tc_expected if expose_io else None,
                            "actual": None,
                        })
                        continue

                    actual = result["stdout"].strip()
                    passed = actual == tc_expected

                    results.append({
                        "passed": passed,
                        "runtime_ms": elapsed_ms,
                        "memory_kb": result.get("memory_kb", 0),
                        "input": tc_input if expose_io else None,
                        "expected": tc_expected if expose_io else None,
                        "actual": actual if expose_io else None,
                        "error": None if passed else f"Expected: {tc_expected!r}\nActual: {actual!r}" if expose_io else "Test case failed",
                    })

                except Exception as e:
                    results.append({
                        "passed": False,
                        "error_type": "RuntimeError",
                        "error": str(e)[:300],
                        "runtime_ms": 0,
                        "memory_kb": 0,
                        "input": tc_input if expose_io else None,
                        "expected": tc_expected if expose_io else None,
                        "actual": None,
                    })

        return results


# ─── Language Compilers ───────────────────────────────────────────────────────

def _compile_java(src_path: str, out_dir: str) -> Optional[str]:
    """Compile Java source. Returns error string or None on success."""
    javac = shutil.which("javac")
    if not javac:
        return "Java compiler (javac) not found on system PATH."
    try:
        proc = subprocess.run(
            [javac, "-d", out_dir, src_path],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECS
        )
        if proc.returncode != 0:
            return (proc.stderr or proc.stdout).strip()[:1000]
        return None
    except subprocess.TimeoutExpired:
        return "Compilation timed out."
    except Exception as e:
        return str(e)


def _compile_cpp(src_path: str, out_path: str) -> Optional[str]:
    """Compile C++ source. Returns error string or None on success."""
    gpp = shutil.which("g++")
    if not gpp:
        return "C++ compiler (g++) not found on system PATH."
    try:
        proc = subprocess.run(
            [gpp, "-O2", "-o", out_path, src_path, "-std=c++17"],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECS
        )
        if proc.returncode != 0:
            return (proc.stderr or proc.stdout).strip()[:1000]
        return None
    except subprocess.TimeoutExpired:
        return "Compilation timed out."
    except Exception as e:
        return str(e)


def _compile_typescript(src_path: str, js_out_path: str) -> Optional[str]:
    """Compile TypeScript to JavaScript. Returns error string or None on success."""
    tsc = shutil.which("tsc")
    if not tsc:
        return "TypeScript compiler (tsc) not found on system PATH. Install with: npm i -g typescript"
    try:
        proc = subprocess.run(
            [tsc, "--target", "ES2020", "--module", "commonjs", "--outDir",
             os.path.dirname(js_out_path), "--strict", src_path],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECS,
        )
        if proc.returncode != 0:
            return (proc.stderr or proc.stdout).strip()[:1000]
        return None
    except subprocess.TimeoutExpired:
        return "TypeScript compilation timed out."
    except Exception as e:
        return str(e)


# ─── Subprocess Runner ────────────────────────────────────────────────────────

def _run_subprocess(cmd: List[str], stdin_input: str, timeout: int) -> Dict:
    """Run a command, capturing stdout/stderr, with timeout. Estimates memory via resource module on Unix."""
    import resource
    try:
        def _set_limits():
            try:
                resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_KB * 1024, MEMORY_LIMIT_KB * 1024))
            except (ValueError, OSError):
                pass

        proc = subprocess.run(
            cmd,
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "/tmp"), "TMPDIR": os.environ.get("TMPDIR", "/tmp")},
            preexec_fn=_set_limits if hasattr(resource, "setrlimit") else None,
        )

        # Try to estimate memory from /proc/self/status on Linux
        memory_kb = 0
        try:
            if hasattr(proc, "pid") and os.path.exists(f"/proc/{proc.pid}/status"):
                with open(f"/proc/{proc.pid}/status") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            memory_kb = int(line.split()[1])
                            break
        except Exception:
            pass

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
            "memory_kb": memory_kb,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": 1, "stdout": "", "stderr": "", "timed_out": True, "memory_kb": 0}
    except FileNotFoundError as e:
        return {"returncode": 1, "stdout": "", "stderr": str(e), "timed_out": False, "memory_kb": 0}


# ─── Docker Runner ────────────────────────────────────────────────────────────

def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


def _run_docker_python(src_path: str, stdin_input: str, timeout: int) -> Dict:
    """Run Python code in Docker sandbox."""
    try:
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "128m",
            "--cpus", "0.5",
            "-i",
            "-v", f"{src_path}:/sandbox/solution.py:ro",
            "python:3.11-slim",
            "python", "/sandbox/solution.py",
        ]
        proc = subprocess.run(
            cmd, input=stdin_input, capture_output=True, text=True, timeout=timeout
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
            "memory_kb": 0,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": 1, "stdout": "", "stderr": "", "timed_out": True, "memory_kb": 0}
    except Exception:
        # Docker failed — fall back to local
        return _run_subprocess([sys.executable, src_path], stdin_input, timeout)


# ─── Utilities ────────────────────────────────────────────────────────────────

def _build_output_summary(results: List[Dict]) -> str:
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    if total == 0:
        return "No test cases to evaluate."
    if passed == total:
        return f"All {total} test case(s) passed!"
    lines = [f"{passed}/{total} test case(s) passed."]
    for i, r in enumerate(results):
        if not r["passed"] and r.get("error"):
            lines.append(f"\nTest {i+1}: {r['error'][:200]}")
    return "\n".join(lines)

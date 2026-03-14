import json
import shutil
import subprocess
import tempfile
from json import JSONDecodeError
from pathlib import Path


TEMP_ROOT = Path(__file__).resolve().parents[3] / ".codex-tmp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


DISALLOWED_PATTERNS = [
    "import os",
    "import sys",
    "subprocess",
    "open(",
    "eval(",
    "exec(",
    "require('fs')",
    "require(\"fs\")",
    "child_process",
    "process.exit",
]


def execute_code(
    *,
    language: str,
    code: str,
    function_name: str,
    test_cases: list[dict],
) -> dict:
    lower_code = code.lower()
    for pattern in DISALLOWED_PATTERNS:
        if pattern in lower_code:
            return {
                "passed": 0,
                "total": len(test_cases),
                "results": [
                    {
                        "status": "rejected",
                        "message": f"Disallowed code pattern detected: {pattern}",
                    }
                ],
            }

    suffix = ".py" if language == "python" else ".js"
    runner = _build_python_runner if language == "python" else _build_javascript_runner
    program = runner(code, function_name, test_cases)

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(dir=TEMP_ROOT)
        file_path = Path(temp_dir) / f"runner{suffix}"
        file_path.write_text(program, encoding="utf-8")
        command = ["python", str(file_path)] if language == "python" else ["node", str(file_path)]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except FileNotFoundError:
            runtime = "Python" if language == "python" else "Node.js"
            return {
                "passed": 0,
                "total": len(test_cases),
                "results": [
                    {
                        "status": "error",
                        "message": f"{runtime} runtime is not installed or not available on PATH.",
                    }
                ],
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "total": len(test_cases),
                "results": [
                    {
                        "status": "error",
                        "message": "Code execution timed out.",
                    }
                ],
            }
        if completed.returncode != 0:
            return {
                "passed": 0,
                "total": len(test_cases),
                "results": [
                    {
                        "status": "error",
                        "message": completed.stderr.strip() or completed.stdout.strip() or "Execution failed",
                    }
                ],
            }
        raw_output = completed.stdout.strip()
        if not raw_output:
            return {
                "passed": 0,
                "total": len(test_cases),
                "results": [
                    {
                        "status": "error",
                        "message": "Code runner produced no output.",
                    }
                ],
            }
        try:
            payload = json.loads(raw_output)
        except JSONDecodeError:
            return {
                "passed": 0,
                "total": len(test_cases),
                "results": [
                    {
                        "status": "error",
                        "message": completed.stderr.strip() or raw_output[:500],
                    }
                ],
            }
        return {
            "passed": int(payload.get("passed", 0)),
            "total": int(payload.get("total", len(test_cases))),
            "results": payload.get("results", []),
        }
    except PermissionError:
        return {
            "passed": 0,
            "total": len(test_cases),
            "results": [
                {
                    "status": "error",
                    "message": "Local code execution is blocked by filesystem permissions in this environment.",
                }
            ],
        }
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _build_python_runner(code: str, function_name: str, test_cases: list[dict]) -> str:
    return f"""
import json
{code}
test_cases = {json.dumps(test_cases)}
results = []
passed = 0
for case in test_cases:
    try:
        actual = {function_name}(*case.get("input", []))
        expected = case.get("expected")
        status = "passed" if actual == expected else "failed"
        if status == "passed":
            passed += 1
        results.append({{"input": case.get("input", []), "expected": expected, "actual": actual, "status": status}})
    except Exception as exc:
        results.append({{"input": case.get("input", []), "status": "error", "message": str(exc)}})
print(json.dumps({{"passed": passed, "total": len(test_cases), "results": results}}, default=str))
""".strip()


def _build_javascript_runner(code: str, function_name: str, test_cases: list[dict]) -> str:
    return f"""
{code}
const testCases = {json.dumps(test_cases)};
const results = [];
let passed = 0;
const targetFunction =
  typeof {function_name} === "function"
    ? {function_name}
    : typeof globalThis.{function_name} === "function"
      ? globalThis.{function_name}
      : null;
for (const testCase of testCases) {{
  try {{
    if (!targetFunction) {{
      throw new TypeError("Function {function_name} is not defined");
    }}
    const actual = targetFunction(...(testCase.input || []));
    const expected = testCase.expected;
    const status = JSON.stringify(actual) === JSON.stringify(expected) ? "passed" : "failed";
    if (status === "passed") passed += 1;
    results.push({{ input: testCase.input || [], expected, actual, status }});
  }} catch (error) {{
    results.push({{ input: testCase.input || [], status: "error", message: String(error) }});
  }}
}}
console.log(JSON.stringify({{ passed, total: testCases.length, results }}));
""".strip()


def analyze_complexity(code: str) -> dict:
    normalized = code.lower()
    suggestions: list[str] = []
    observations: list[str] = []

    nested_loops = normalized.count("for ") + normalized.count("while ")
    if nested_loops >= 2:
        time_complexity = "O(n^2)"
        suggestions.append("Reduce nested iteration if a hash-based lookup can replace one loop.")
    elif "sort(" in normalized or ".sort(" in normalized or "sorted(" in normalized:
        time_complexity = "O(n log n)"
        observations.append("Sorting dominates the runtime.")
    elif "for " in normalized or "while " in normalized:
        time_complexity = "O(n)"
    else:
        time_complexity = "O(1) to O(log n)"

    if "dict" in normalized or "map" in normalized or "{}" in normalized:
        observations.append("Hash-based structures are used, which may improve lookup speed.")
    if "recursion" in normalized or ("def " in normalized and normalized.count("return") > 1):
        observations.append("Check recursion depth and stack usage if the solution is recursive.")
    if not suggestions:
        suggestions.append("Add a short explanation of dominant operations to justify the complexity claim.")

    return {
        "time_complexity": time_complexity,
        "suggestions": suggestions[:3],
        "observations": observations[:3],
    }

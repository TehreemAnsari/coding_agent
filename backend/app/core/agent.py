import json
import re
from typing import Any, List, Tuple, Dict
from .llm import call_llm
from .runner import run
from ..utils.file_ops import save_run

def parse_test_cases(raw: List[List[Any]]) -> List[Tuple[List[Any], Any]]:
    parsed = []
    for item in raw:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("Each test case must be [ [args...], expected ]")
        inp, expected = item
        if not isinstance(inp, list):
            raise ValueError("Inputs must be a list of args")
        parsed.append((inp, expected))
    return parsed

def solve_problem(problem: str, test_cases: List[Tuple[List[Any], Any]], enable_reflection: bool = False, max_retries: int = 1) -> Dict:
    examples = [{"inputs": tc[0], "expected": tc[1]} for tc in test_cases[:3]]

    code = call_llm(problem, examples)
    record = run(problem, code, test_cases, llm_trajectory=[{"generated": code}])

    retries = 0
    while enable_reflection and retries < max_retries and record["score"] < 1.0 and not record.get("error"):
        failures = [r for r in record["test_cases"] if not r["passed"]]
        feedback = {
            "instruction": "The previous solution failed these cases. Fix the logic and return corrected code only.",
            "failing": failures[:3],
        }
        revised_prompt = problem + "\n\nNotes from tests:\n" + json.dumps(feedback)
        revised_code = call_llm(revised_prompt, examples)
        record = run(problem, revised_code, test_cases, llm_trajectory=record.get("llm_trajectory", []) + [{"revised": revised_code}])
        retries += 1

    save_run(record)
    return record

from pydantic import BaseModel
from typing import Any, List, Optional

class GenerateRequest(BaseModel):
    problem: str
    test_cases: List[List[Any]]

class TestResult(BaseModel):
    input: str
    expected_output: str
    output: Optional[str] = None
    passed: bool
    error: Optional[str] = None
    runtime_ms: Optional[int] = None

class GenerateResponse(BaseModel):
    id: str
    solution_code: str
    results: List[TestResult]
    score: float
    test_cases_generated: bool = False
    error: Optional[str] = None

class RunSummary(BaseModel):
    run_id: str
    timestamp: str
    score: float
    problem_preview: str

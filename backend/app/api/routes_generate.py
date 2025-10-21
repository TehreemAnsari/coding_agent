from fastapi import APIRouter, HTTPException
from ..models.problem import GenerateRequest, GenerateResponse, TestResult
from ..core.agent import solve_problem, parse_test_cases

router = APIRouter()

@router.post("/generate_solution", response_model=GenerateResponse)
def generate_solution(req: GenerateRequest):
    try:
        testcases = parse_test_cases(req.test_cases)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid test cases format: {str(e)}")
    
    try:
        record = solve_problem(req.problem, testcases, enable_reflection=False)
        
        test_results = [
            TestResult(
                input=tc["input"],
                expected_output=tc["expected_output"],
                output=tc.get("output"),
                passed=tc["passed"],
                error=tc.get("error"),
                runtime_ms=tc.get("runtime_ms")
            )
            for tc in record["test_cases"]
        ]
        
        return GenerateResponse(
            id=record["run_id"],
            solution_code=record["solution_code"],
            results=test_results,
            score=record["score"],
            error=record.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating solution: {str(e)}")

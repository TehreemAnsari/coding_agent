import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.agent import solve_problem, parse_test_cases

def evaluate(eval_set_path: str = "eval_set.json"):
    with open(eval_set_path, "r") as f:
        eval_set = json.load(f)
    
    total_tests = 0
    total_passed = 0
    results = []
    
    print("=" * 80)
    print("CODE-SOLVER AGENT EVALUATION")
    print("=" * 80)
    print()
    
    for i, item in enumerate(eval_set, 1):
        problem = item["problem"]
        test_cases = parse_test_cases(item["test_cases"])
        
        print(f"Problem {i}/{len(eval_set)}: {problem[:60]}...")
        
        try:
            record = solve_problem(problem, test_cases, enable_reflection=False)
            passed = sum(1 for tc in record["test_cases"] if tc["passed"])
            total = len(record["test_cases"])
            
            total_tests += total
            total_passed += passed
            
            result = {
                "problem": problem,
                "score": record["score"],
                "passed": passed,
                "total": total,
                "run_id": record["run_id"]
            }
            results.append(result)
            
            print(f"  Score: {record['score']:.2%} ({passed}/{total})")
            
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "problem": problem,
                "score": 0.0,
                "passed": 0,
                "total": len(test_cases),
                "error": str(e)
            })
            total_tests += len(test_cases)
        
        print()
    
    eval_score = total_passed / total_tests if total_tests > 0 else 0.0
    
    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Overall Score: {eval_score:.2%}")
    print(f"Total Tests Passed: {total_passed}/{total_tests}")
    print()
    
    eval_result = {
        "eval_score": eval_score,
        "total_passed": total_passed,
        "total_tests": total_tests,
        "results": results
    }
    
    with open("runs/eval_history.json", "w") as f:
        json.dump(eval_result, f, indent=2)
    
    print(f"Results saved to runs/eval_history.json")
    
    return eval_score

if __name__ == "__main__":
    score = evaluate()
    sys.exit(0 if score >= 0.8 else 1)

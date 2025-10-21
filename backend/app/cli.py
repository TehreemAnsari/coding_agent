import argparse
import json
import sys
from .core.agent import solve_problem, parse_test_cases

def main():
    parser = argparse.ArgumentParser(description="Code-Solver Agent CLI")
    parser.add_argument("--problem", required=True, help="The coding problem description")
    parser.add_argument("--test-cases", required=True, help="Test cases as JSON array: [[[args], expected], ...]")
    parser.add_argument("--reflection", action="store_true", help="Enable self-reflection loop")
    parser.add_argument("--retries", type=int, default=1, help="Max retries for reflection (default: 1)")
    
    args = parser.parse_args()
    
    try:
        test_cases_raw = json.loads(args.test_cases)
        test_cases = parse_test_cases(test_cases_raw)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in test cases: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Running Code-Solver Agent...")
    print(f"Problem: {args.problem}")
    print(f"Test cases: {len(test_cases)}")
    print()
    
    try:
        record = solve_problem(
            args.problem, 
            test_cases, 
            enable_reflection=args.reflection,
            max_retries=args.retries
        )
        
        print("=" * 80)
        print("RESULT")
        print("=" * 80)
        print(json.dumps(record, indent=2))
        print()
        print(f"Run ID: {record['run_id']}")
        print(f"Score: {record['score']:.2%}")
        print(f"Passed: {sum(1 for tc in record['test_cases'] if tc['passed'])}/{len(record['test_cases'])}")
        
        if record.get("error"):
            print(f"Error: {record['error']}")
            sys.exit(1)
        
        if record['score'] < 1.0:
            sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

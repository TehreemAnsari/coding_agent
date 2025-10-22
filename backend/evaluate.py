import json
import sys
import os
from typing import List, Dict, Any, Optional
sys.path.insert(0, os.path.dirname(__file__))

from app.core.agent import CodeSolverAgent


class Evaluator:
    """
    Evaluation system for benchmarking the Code-Solver Agent.
    
    Supports filtering, multiple runs, and detailed metrics aggregation.
    """
    
    def __init__(self, agent: Optional[CodeSolverAgent] = None, 
                 output_file: str = "runs/eval_history.json"):
        """
        Initialize Evaluator with agent and output configuration.
        
        Args:
            agent: CodeSolverAgent instance to evaluate
            output_file: Path to save evaluation results
        """
        self.agent = agent or CodeSolverAgent()
        self.output_file = output_file
    
    def evaluate(self, eval_set_path: str = "eval_set.json", 
                 problem_filter: Optional[List[int]] = None,
                 enable_reflection: bool = False,
                 max_retries: int = 1,
                 verbose: bool = True) -> Dict[str, Any]:
        """
        Run evaluation on a set of problems.
        
        Args:
            eval_set_path: Path to evaluation dataset
            problem_filter: List of problem indices to evaluate (None for all)
            enable_reflection: Whether to enable self-reflection
            max_retries: Maximum reflection retries
            verbose: Whether to print progress
            
        Returns:
            Dictionary with evaluation results and metrics
        """
        with open(eval_set_path, "r") as f:
            eval_set = json.load(f)
        
        # Apply problem filter if specified
        if problem_filter is not None:
            eval_set = [eval_set[i] for i in problem_filter if 0 <= i < len(eval_set)]
        
        total_tests = 0
        total_passed = 0
        results = []
        
        if verbose:
            print("=" * 80)
            print("CODE-SOLVER AGENT EVALUATION")
            print("=" * 80)
            print()
        
        for i, item in enumerate(eval_set, 1):
            problem = item["problem"]
            test_cases = self.agent.parse_test_cases(item["test_cases"])
            
            if verbose:
                print(f"Problem {i}/{len(eval_set)}: {problem[:60]}...")
            
            try:
                record = self.agent.solve_problem(
                    problem, test_cases, 
                    enable_reflection=enable_reflection, 
                    max_retries=max_retries
                )
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
                
                if verbose:
                    print(f"  Score: {record['score']:.2%} ({passed}/{total})")
                
            except Exception as e:
                if verbose:
                    print(f"  Error: {e}")
                results.append({
                    "problem": problem,
                    "score": 0.0,
                    "passed": 0,
                    "total": len(test_cases),
                    "error": str(e)
                })
                total_tests += len(test_cases)
            
            if verbose:
                print()
        
        eval_score = total_passed / total_tests if total_tests > 0 else 0.0
        
        if verbose:
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
            "results": results,
            "config": {
                "enable_reflection": enable_reflection,
                "max_retries": max_retries,
                "problem_filter": problem_filter
            }
        }
        
        # Save results
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, "w") as f:
            json.dump(eval_result, f, indent=2)
        
        if verbose:
            print(f"Results saved to {self.output_file}")
        
        return eval_result
    
    def evaluate_subset(self, eval_set_path: str, start_idx: int, end_idx: int, 
                        **kwargs) -> Dict[str, Any]:
        """
        Evaluate a subset of problems by index range.
        
        Args:
            eval_set_path: Path to evaluation dataset
            start_idx: Starting problem index (inclusive)
            end_idx: Ending problem index (exclusive)
            **kwargs: Additional arguments passed to evaluate()
            
        Returns:
            Dictionary with evaluation results
        """
        problem_filter = list(range(start_idx, end_idx))
        return self.evaluate(eval_set_path, problem_filter=problem_filter, **kwargs)
    
    def compare_models(self, eval_set_path: str, models: List[str], 
                      **kwargs) -> Dict[str, Any]:
        """
        Compare performance across different LLM models.
        
        Args:
            eval_set_path: Path to evaluation dataset
            models: List of model names to compare
            **kwargs: Additional arguments passed to evaluate()
            
        Returns:
            Dictionary with comparison results
        """
        comparison_results = {}
        
        for model in models:
            print(f"\nEvaluating with model: {model}")
            custom_llm = self.agent.llm.__class__(model=model)
            custom_agent = CodeSolverAgent(llm=custom_llm, runner=self.agent.runner)
            
            evaluator = Evaluator(agent=custom_agent, output_file=f"runs/eval_{model}.json")
            result = evaluator.evaluate(eval_set_path, verbose=False, **kwargs)
            comparison_results[model] = result
        
        return comparison_results


# Backward compatibility function
def evaluate(eval_set_path: str = "eval_set.json"):
    """Backward compatibility function."""
    evaluator = Evaluator()
    result = evaluator.evaluate(eval_set_path)
    return result["eval_score"]


if __name__ == "__main__":
    score = evaluate()
    sys.exit(0 if score >= 0.8 else 1)

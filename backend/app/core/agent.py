import json
import re
from typing import Any, List, Tuple, Dict, Optional
from .llm import OpenAILLM
from .runner import CodeRunner
from ..utils.file_ops import save_run


class CodeSolverAgent:
    """
    Main orchestration class for solving coding problems.
    
    Coordinates LLM code generation, code execution, and self-reflection loops.
    """
    
    def __init__(self, llm: Optional[OpenAILLM] = None, runner: Optional[CodeRunner] = None):
        """
        Initialize CodeSolverAgent with dependencies.
        
        Args:
            llm: OpenAILLM instance for code generation
            runner: CodeRunner instance for code execution
        """
        self.llm = llm or OpenAILLM()
        self.runner = runner or CodeRunner()
    
    @staticmethod
    def parse_test_cases(raw: List[List[Any]]) -> List[Tuple[List[Any], Any]]:
        """Parse and validate test cases from raw input."""
        parsed = []
        for item in raw:
            if not isinstance(item, list) or len(item) != 2:
                raise ValueError("Each test case must be [ [args...], expected ]")
            inp, expected = item
            if not isinstance(inp, list):
                raise ValueError("Inputs must be a list of args")
            parsed.append((inp, expected))
        return parsed
    
    def solve_problem(self, problem: str, test_cases: List[Tuple[List[Any], Any]], 
                     enable_reflection: bool = False, max_retries: int = 1) -> Dict[str, Any]:
        """
        Solve a coding problem with optional self-reflection.
        
        Args:
            problem: Description of the coding problem
            test_cases: List of (input, expected_output) tuples
            enable_reflection: Whether to enable self-reflection on failures
            max_retries: Maximum number of reflection attempts
            
        Returns:
            Dictionary with solution results and metadata
        """
        examples = [{"inputs": tc[0], "expected": tc[1]} for tc in test_cases[:3]]

        # Generate initial code
        code = self.llm.generate_code(problem, examples)
        record = self.runner.run_tests(problem, code, test_cases, llm_trajectory=[{"generated": code}])

        # Self-reflection loop
        retries = 0
        while enable_reflection and retries < max_retries and record["score"] < 1.0 and not record.get("error"):
            failures = [r for r in record["test_cases"] if not r["passed"]]
            feedback = {
                "instruction": "The previous solution failed these cases. Fix the logic and return corrected code only.",
                "failing": failures[:3],
            }
            revised_prompt = problem + "\n\nNotes from tests:\n" + json.dumps(feedback)
            revised_code = self.llm.generate_code(revised_prompt, examples)
            record = self.runner.run_tests(
                problem, revised_code, test_cases, 
                llm_trajectory=record.get("llm_trajectory", []) + [{"revised": revised_code}]
            )
            retries += 1

        # Save results
        save_run(record)
        return record
    
    def solve_with_custom_llm(self, problem: str, test_cases: List[Tuple[List[Any], Any]], 
                             custom_llm: OpenAILLM, enable_reflection: bool = False, 
                             max_retries: int = 1) -> Dict[str, Any]:
        """
        Solve a problem with a custom LLM instance.
        
        Args:
            problem: Description of the coding problem
            test_cases: List of (input, expected_output) tuples
            custom_llm: Custom OpenAILLM instance to use
            enable_reflection: Whether to enable self-reflection
            max_retries: Maximum number of reflection attempts
            
        Returns:
            Dictionary with solution results and metadata
        """
        # Temporarily replace LLM
        original_llm = self.llm
        self.llm = custom_llm
        
        try:
            result = self.solve_problem(problem, test_cases, enable_reflection, max_retries)
        finally:
            # Restore original LLM
            self.llm = original_llm
            
        return result


# Backward compatibility functions
def parse_test_cases(raw: List[List[Any]]) -> List[Tuple[List[Any], Any]]:
    """Backward compatibility function."""
    return CodeSolverAgent.parse_test_cases(raw)


def solve_problem(problem: str, test_cases: List[Tuple[List[Any], Any]], 
                 enable_reflection: bool = False, max_retries: int = 1) -> Dict[str, Any]:
    """Backward compatibility function."""
    agent = CodeSolverAgent()
    return agent.solve_problem(problem, test_cases, enable_reflection, max_retries)

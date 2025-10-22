"""
Core logic module for the Code-Solver Agent.

This module contains the main business logic for problem solving,
code generation, and execution.
"""

# Class-based imports
from .agent import CodeSolverAgent
from .runner import CodeRunner
from .llm import OpenAILLM

# Backward compatibility function imports
from .agent import solve_problem, parse_test_cases
from .runner import run
from .llm import call_llm

__all__ = [
    # Classes
    'CodeSolverAgent',
    'CodeRunner', 
    'OpenAILLM',
    # Backward compatibility functions
    'solve_problem',
    'parse_test_cases', 
    'run',
    'call_llm'
]

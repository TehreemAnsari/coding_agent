"""
Code-Solver Agent Backend

A full-stack AI-powered coding problem solver that uses LLMs to generate 
Python solutions, executes them against test cases, and provides detailed 
scoring and results.

This package provides:
- Core problem-solving logic
- API endpoints for web interface
- Data models and schemas
- Utility functions for file operations
"""

from .main import app

__all__ = ['app']

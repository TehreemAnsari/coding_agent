"""
API routes module for the Code-Solver Agent.

This module contains all FastAPI route handlers organized by functionality.
"""

from .routes_generate import router as generate_router
from .routes_results import router as results_router

__all__ = [
    'generate_router',
    'results_router'
]

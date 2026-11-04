"""
FastAPI application proxy for backend.app.main -> backend.main:app.
Ensures compatibility with any launcher targeting backend.app.main.
"""

from backend.main import app

__all__ = ["app"]

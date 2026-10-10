"""Alembic migration environment for the Samanvay-AI backend.

The baseline revision (`versions/0001_baseline.py`) reproduces the schema that
`Base.metadata` already produces, so a fresh database can be created from
versioned migrations instead of `create_all()`.  No authentication
architecture is introduced or changed here.
"""

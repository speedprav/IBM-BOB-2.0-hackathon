"""
Vercel serverless entry point for DevTwin FastAPI backend.
Vercel's Python runtime discovers `app` from this file at the service root.
"""
from main import app  # noqa: F401 — re-exported for Vercel

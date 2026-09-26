"""
Vercel serverless entry point for DevTwin FastAPI backend.
Vercel looks for a module-level `app` (ASGI callable) in this file.
"""
import sys
import os

# Ensure backend root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app  # noqa: F401 — Vercel discovers this ASGI app

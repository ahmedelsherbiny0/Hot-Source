"""
Vercel Serverless Function Entrypoint.
Delegates to unified Backend/api/index.py.
"""
import sys
from pathlib import Path

# Add Backend to python path so imports resolve cleanly
backend_path = Path(__file__).resolve().parent.parent / "Backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from api.index import app  # noqa: F401, E402

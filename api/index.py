"""
Vercel Serverless Function Entrypoint.
Delegates to unified Backend/api/index.py.
"""
import sys
from pathlib import Path
import importlib.util
import api

# Ensure Backend directory is on sys.path and extend api package path
backend_dir = Path(__file__).resolve().parent.parent / "Backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

backend_api_dir = str(backend_dir / "api")
if hasattr(api, "__path__") and backend_api_dir not in api.__path__:
    api.__path__.append(backend_api_dir)

backend_index = backend_dir / "api" / "index.py"
spec = importlib.util.spec_from_file_location("backend_app_module", str(backend_index))
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load module spec from {backend_index}")
backend_module = importlib.util.module_from_spec(spec)
sys.modules["backend_app_module"] = backend_module
spec.loader.exec_module(backend_module)

app = backend_module.app

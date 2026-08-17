import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
os.chdir(backend_path)

# Import app from backend directory
import uvicorn
import importlib
backend_main = importlib.import_module("main")
app = getattr(backend_main, "app")
settings = getattr(backend_main, "settings")

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG_MODE)

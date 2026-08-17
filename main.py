import sys
import os
import importlib.util

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

spec = importlib.util.spec_from_file_location("backend_main", os.path.join(backend_dir, "main.py"))
backend_main = importlib.util.module_from_spec(spec)
sys.modules["backend_main"] = backend_main
spec.loader.exec_module(backend_main)

app = backend_main.app
settings = backend_main.settings
run_db_migrations = getattr(backend_main, "run_db_migrations", None)
seed_initial_data = getattr(backend_main, "seed_initial_data", None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG_MODE)

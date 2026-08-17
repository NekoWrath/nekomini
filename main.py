import sys
import os
import runpy

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
os.chdir(backend_path)

if __name__ == "__main__":
    runpy.run_path(os.path.join(backend_path, "main.py"), run_name="__main__")

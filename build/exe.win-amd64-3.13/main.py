# Shim to prefer the updated repository `main.py` when running the frozen executable.
# This lets the frozen runtime import the workspace source, so fixes here apply immediately.
import sys
import os

# Repo root is three levels up from this build folder (../.. -> build -> repo root)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

try:
    # Import the project's main from the workspace
    from main import main as app_main
except Exception:
    # Fall back to the embedded frozen module
    try:
        import importlib
        mod = importlib.import_module('main')
        app_main = getattr(mod, 'main')
    except Exception:
        raise

if __name__ == '__main__':
    app_main()

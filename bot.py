"""Launch the same Discord worker locally, keeping existing SQLite rules."""
import os
from pathlib import Path
import runpy

root = Path(__file__).resolve().parent
os.environ.setdefault("RULES_DB", str(root / "rules.sqlite3"))
runpy.run_path(str(root / "dashboard" / "worker" / "worker.py"), run_name="__main__")

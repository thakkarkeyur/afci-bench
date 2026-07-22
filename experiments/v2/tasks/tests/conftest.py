"""Make the public-task validator importable when tests run from anywhere."""
import sys
from pathlib import Path

# experiments/v2/tasks (parent of this tests/ dir) holds validate_public_tasks.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

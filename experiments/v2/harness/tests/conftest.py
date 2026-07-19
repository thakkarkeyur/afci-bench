"""Make the harness package importable when tests run from anywhere."""
import sys
from pathlib import Path

# experiments/v2/harness (parent of this tests/ dir) holds context_audit.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

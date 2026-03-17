"""
conftest.py — Auto-adds the project root to sys.path so that
`pytest tests/` works without setting PYTHONPATH explicitly.
"""
import sys
from pathlib import Path

# Insert project root at the front of sys.path
sys.path.insert(0, str(Path(__file__).parent))

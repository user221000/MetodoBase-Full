#!/usr/bin/env python3
"""
run_pipeline.py — Entry point for the multi-agent pipeline.

Usage:
    python run_pipeline.py
    python run_pipeline.py "Analyze the authentication module"
"""

import json
import sys
from pathlib import Path

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from orchestrator.pipeline import run_pipeline

DEFAULT_INPUT = """Analyze the MetodoBase nutrition SaaS platform.
The platform serves gyms and independent nutritionists.
It includes: meal plan generation, PDF export, client management, dashboard, and billing.
Tech stack: Python backend, PySide6 desktop UI, FastAPI web API, SQLite/PostgreSQL.

Focus areas:
1. Identify architectural issues and technical debt
2. Propose monetizable features for gym owners
3. Implement the highest-priority improvement
4. Verify the implementation quality"""


def main():
    input_text = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT

    print("Pipeline input:")
    print("─" * 40)
    print(input_text[:300])
    if len(input_text) > 300:
        print("...")
    print("─" * 40)

    result = run_pipeline(input_text)

    logs_dir = ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    result_path = logs_dir / "pipeline-result.json"
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nFull result saved to: {result_path}")


if __name__ == "__main__":
    main()

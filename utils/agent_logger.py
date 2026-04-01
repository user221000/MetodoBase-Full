"""
utils/agent_logger.py — Per-agent JSON logging.

Saves structured logs to logs/{agent_name}.json (appends to array).
"""

import json
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def log_agent_output(agent_name: str, data: dict) -> None:
    """
    Append agent output to its JSON log file.

    Args:
        agent_name: Agent role name (architect, product, etc.)
        data: Data to log
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"{agent_name}.json"

    existing = []
    if log_path.exists():
        try:
            content = log_path.read_text(encoding="utf-8")
            parsed = json.loads(content)
            existing = parsed if isinstance(parsed, list) else [parsed]
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(data)
    log_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def read_agent_logs(agent_name: str) -> list:
    """Read all logs for a specific agent."""
    log_path = LOGS_DIR / f"{agent_name}.json"
    if not log_path.exists():
        return []
    try:
        parsed = json.loads(log_path.read_text(encoding="utf-8"))
        return parsed if isinstance(parsed, list) else [parsed]
    except (json.JSONDecodeError, OSError):
        return []

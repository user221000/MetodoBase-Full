"""
orchestrator/run_agent.py — Core function to run a single LLM agent.

Loads the system prompt from agents/{role}.prompt.txt, calls the OpenAI-compatible
API, parses the JSON response, and retries on failure.
"""

import json
import os
import time
from pathlib import Path

import requests

from utils.parse_json import parse_json
from utils.agent_logger import log_agent_output

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
MAX_RETRIES = 2


def run_agent(role: str, user_input: str) -> dict:
    """
    Run a single agent: load prompt, call LLM, parse JSON response.

    Args:
        role: Agent name (architect|product|engineer|qa)
        user_input: The user message / context to send

    Returns:
        Parsed JSON dict from the agent
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    prompt_path = AGENTS_DIR / f"{role}.prompt.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    system_prompt = prompt_path.read_text(encoding="utf-8").strip()

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": model,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=120,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"API returned {response.status_code}: {response.text[:500]}"
                )

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")

            if not content:
                raise RuntimeError("Empty response from LLM")

            parsed = parse_json(content)

            log_agent_output(role, {
                "attempt": attempt + 1,
                "model": model,
                "input": user_input[:200],
                "output": parsed,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })

            return parsed

        except Exception as err:
            last_error = err
            is_last = attempt == MAX_RETRIES
            print(f"  [{role}] Attempt {attempt + 1}/{MAX_RETRIES + 1} failed: {err}")
            if not is_last:
                time.sleep(1 * (attempt + 1))

    raise RuntimeError(
        f'Agent "{role}" failed after {MAX_RETRIES + 1} attempts: {last_error}'
    )

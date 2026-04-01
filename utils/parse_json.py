"""
utils/parse_json.py — Safe JSON parser for LLM responses.

Handles markdown fences, trailing commas, and noisy responses.
"""

import json
import re


def parse_json(raw: str) -> dict:
    """
    Parse JSON from an LLM response, handling common formatting issues.

    Args:
        raw: Raw string from LLM response

    Returns:
        Parsed dict

    Raises:
        ValueError: If parsing fails after cleanup
    """
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("parse_json: received empty or non-string input")

    cleaned = raw.strip()

    # Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Remove trailing commas before closing brackets/braces
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as first_error:
        # Try extracting first JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                extracted = re.sub(r",\s*([}\]])", r"\1", match.group(0))
                return json.loads(extracted)
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"parse_json: failed to parse LLM response. "
            f"First 200 chars: \"{raw[:200]}\". "
            f"Error: {first_error}"
        )

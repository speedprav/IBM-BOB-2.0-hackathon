"""
Shared JSON extraction helper for all agents.
Handles Gemini's tendency to wrap JSON in markdown code fences.
"""
from __future__ import annotations
import json
import re


def extract_json(raw: str):
    """
    Robustly extract JSON from an LLM response.
    Handles:
    - Plain JSON
    - ```json ... ``` fences
    - ``` ... ``` fences
    - Leading/trailing whitespace
    """
    text = raw.strip()

    # 1. Direct parse — works when Gemini returns clean JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract from code fence  ```json ... ``` or ``` ... ```
    fence_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 3. Find first [ or { and try parsing from there to end
    for start_char in ('[', '{'):
        idx = text.find(start_char)
        if idx != -1:
            try:
                return json.loads(text[idx:])
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not extract JSON from response: {text[:300]}")

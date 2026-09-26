"""
Shared JSON extraction helper for all agents.
Handles Gemini wrapping JSON in markdown fences and truncated output.
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
    - Leading/trailing prose around JSON
    - Truncated JSON (common when max_output_tokens is hit)
    """
    if raw is None:
        raise ValueError("Could not extract JSON from response: <empty>")

    text = str(raw).strip()
    if not text:
        raise ValueError("Could not extract JSON from response: <empty>")

    candidates = _candidate_strings(text)
    last_err: Exception | None = None

    for candidate in candidates:
        for parser in (_loads, _raw_decode, _loads_repaired):
            try:
                return parser(candidate)
            except Exception as e:
                last_err = e

    raise ValueError(f"Could not extract JSON from response: {text[:300]}") from last_err


def _candidate_strings(text: str) -> list[str]:
    """Build ordered list of candidate JSON substrings to try."""
    out: list[str] = [text]

    fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if fence_match:
        out.append(fence_match.group(1).strip())

    # Unclosed fence (model hit token limit mid-block)
    unclosed = re.search(r"```(?:json)?\s*\n?([\s\S]+)$", text)
    if unclosed:
        out.append(unclosed.group(1).strip())

    for start_char in ("[", "{"):
        idx = text.find(start_char)
        if idx != -1:
            out.append(text[idx:].strip())

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in out:
        if c and c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def _loads(s: str):
    return json.loads(s)


def _raw_decode(s: str):
    """Parse the first complete JSON value, ignoring trailing junk."""
    obj, _ = json.JSONDecoder().raw_decode(s)
    return obj


def _loads_repaired(s: str):
    """Close truncated JSON strings / braces / brackets, then parse."""
    return json.loads(_repair_truncated_json(s))


def _repair_truncated_json(s: str) -> str:
    """
    Best-effort repair for truncated JSON arrays/objects.
    Example:  [ {"a": "hel   →  [ {"a": "hel"} ]
    """
    # Drop a trailing incomplete escape
    if s.endswith("\\"):
        s = s[:-1]

    in_string = False
    escape = False
    stack: list[str] = []

    for c in s:
        if escape:
            escape = False
            continue
        if c == "\\" and in_string:
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            stack.append("}")
        elif c == "[":
            stack.append("]")
        elif c in ("}", "]"):
            if stack and stack[-1] == c:
                stack.pop()

    repaired = s
    if in_string:
        repaired += '"'

    # Strip trailing comma / colon after last complete value
    repaired = re.sub(r"[,:]\s*$", "", repaired)

    # If we ended mid-key like `{ "sev` close the string already handled;
    # dangling keys without values → drop back to last comma/brace
    if re.search(r'[{,]\s*"[^"]*"\s*$', repaired):
        repaired = re.sub(r',\s*"[^"]*"\s*$', "", repaired)
        repaired = re.sub(r'\{\s*"[^"]*"\s*$', "{", repaired)

    while stack:
        repaired = re.sub(r",\s*$", "", repaired)
        repaired += stack.pop()

    return repaired

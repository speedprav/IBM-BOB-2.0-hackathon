"""
LLM client — Google Gemini via google-generativeai SDK.

Live mode (GEMINI_API_KEY set): ALWAYS calls Gemini. Never substitutes canned text.
Demo mode (no key): returns pre-computed Demo Orders responses for offline demos only.
"""
from __future__ import annotations
import json
import os
import time
from typing import Optional

# Prefer free-tier-friendly Flash-Lite models first (higher RPM, less quota burn).
# Heavier Flash/Pro models often return 429 with FreeTier limit 0 or exhausted quota.
_GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash",
]
_GEMINI_MODEL = _GEMINI_MODELS[0]

# Populated after each successful live call — used in the analysis report
_last_model_used: Optional[str] = None
_last_mode: str = "unknown"  # "live_gemini" | "demo"


def _has_key() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def is_live_mode() -> bool:
    return _has_key()


def last_model_used() -> Optional[str]:
    return _last_model_used


def last_analysis_mode() -> str:
    return _last_mode


def complete(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    model: str = _GEMINI_MODEL,
    json_mode: bool = True,
) -> str:
    """
    Single-turn completion.
    With GEMINI_API_KEY: live Gemini only (errors bubble up — no silent demo swap).
    Without key: demo canned responses.
    json_mode=True asks Gemini for JSON (agents that parse JSON).
    json_mode=False is for free-form output (e.g. generated Python tests).
    """
    global _last_mode
    if _has_key():
        _last_mode = "live_gemini"
        return _gemini_complete(system_prompt, user_prompt, max_tokens, model, json_mode)

    _last_mode = "demo"
    return _demo_complete(system_prompt, user_prompt)


def _retry_seconds(err: Exception) -> float:
    """Parse Gemini's retry_delay if present; otherwise a short backoff."""
    import re
    text = str(err)
    # e.g. retry_delay { seconds: 29 }
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+(?:\.\d+)?)", text)
    if m:
        return min(float(m.group(1)) + 1.0, 45.0)
    m2 = re.search(r"Please retry in ([\d.]+)s", text, re.I)
    if m2:
        return min(float(m2.group(1)) + 1.0, 45.0)
    return 8.0


def _gemini_complete(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    model: str,
    json_mode: bool = True,
) -> str:
    global _last_model_used
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError(
            "google-generativeai is not installed — cannot run live AI analysis."
        ) from e

    key = os.environ["GEMINI_API_KEY"].strip()
    genai.configure(api_key=key)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    models_to_try = [model] + [m for m in _GEMINI_MODELS if m != model]
    last_err: Exception | None = None
    # Cap total wait so Vercel doesn't kill the request
    quota_retries_left = 2

    base_config = {
        "max_output_tokens": max_tokens,
        "temperature": 0.7,
    }
    configs = []
    if json_mode:
        configs.append({**base_config, "response_mime_type": "application/json"})
    configs.append(dict(base_config))

    for attempt_model in models_to_try:
        for generation_config in configs:
            try:
                m = genai.GenerativeModel(
                    model_name=attempt_model,
                    generation_config=generation_config,
                )
                response = m.generate_content(full_prompt)
                text = getattr(response, "text", None)
                if not text:
                    try:
                        text = response.candidates[0].content.parts[0].text
                    except Exception:
                        text = ""
                if not text or not str(text).strip():
                    raise RuntimeError(f"Empty response from {attempt_model}")
                _last_model_used = attempt_model
                return str(text)
            except Exception as e:
                err_str = str(e)
                last_err = e
                if "response_mime_type" in generation_config and any(
                    x in err_str.lower() for x in ("mime", "invalid", "unsupported", "400")
                ):
                    continue
                if any(x in err_str for x in ("429", "RESOURCE_EXHAUSTED", "quota")):
                    if quota_retries_left > 0:
                        wait = _retry_seconds(e)
                        time.sleep(wait)
                        quota_retries_left -= 1
                        # Retry same model once after waiting
                        try:
                            m = genai.GenerativeModel(
                                model_name=attempt_model,
                                generation_config=generation_config,
                            )
                            response = m.generate_content(full_prompt)
                            text = getattr(response, "text", None) or ""
                            if not text:
                                try:
                                    text = response.candidates[0].content.parts[0].text
                                except Exception:
                                    text = ""
                            if text and str(text).strip():
                                _last_model_used = attempt_model
                                return str(text)
                        except Exception as e2:
                            last_err = e2
                    # Try next model without waiting again
                    break
                if any(x in err_str for x in ("503", "UNAVAILABLE", "404", "NOT_FOUND")):
                    time.sleep(1)
                    break
                time.sleep(0.5)
                break

    raise RuntimeError(
        f"Live Gemini analysis failed after trying {models_to_try}: {last_err}"
    ) from last_err


# ── Demo-only canned responses (used ONLY when GEMINI_API_KEY is unset) ───────

_RISK_RESPONSE = json.dumps([
    {
        "severity": "high",
        "category": "regression",
        "title": "test_cannot_update_confirmed_order will break",
        "description": "The existing test explicitly asserts that updating a confirmed order raises OrderValidationError. The change removes this guard, so the test will fail.",
        "why_it_matters": "A failing test signals that the contract between the service layer and the rest of the system has changed. Merging with a broken test masks the regression.",
        "affected_location": "tests/test_orders.py:TestUpdateOrder.test_cannot_update_confirmed_order",
        "evidence": "Old code: `if not order.can_be_updated()` → raises on CONFIRMED. New code: allows PENDING and CONFIRMED, silently expanding the update window.",
        "suggested_mitigation": "Update or remove the test after explicitly deciding whether confirmed-order updates are intentional, and communicate the contract change to API consumers.",
    },
])

_TEST_RESPONSE = json.dumps({
    "affected_tests": [
        {
            "test_file": "tests/test_orders.py",
            "test_name": "TestUpdateOrder.test_cannot_update_confirmed_order",
            "relevance": "directly_affected",
            "will_break": True,
            "reason": "This test explicitly asserts that updating a CONFIRMED order raises OrderValidationError.",
        }
    ],
    "coverage_gaps": [
        "No test covers updating an order in CONFIRMED status (the new allowed path)",
    ],
})

_DOC_RESPONSE = json.dumps([
    "The architecture doc states: only PENDING orders can be updated (item/notes changes).",
])

_TEST_GEN_RESPONSE = '''\
"""Demo-mode placeholder test — set GEMINI_API_KEY for live generation."""
import pytest

def test_demo_placeholder():
    assert True
'''


def _demo_complete(system_prompt: str, user_prompt: str) -> str:
    """Canned responses — only when no API key is configured."""
    sys_lower = system_prompt.lower()
    user_lower = user_prompt.lower()

    if "documentation analyst" in sys_lower or "documentation" in sys_lower:
        return _DOC_RESPONSE
    if "test engineer" in sys_lower and "regression" not in sys_lower:
        return _TEST_RESPONSE
    if "regression" in sys_lower or "pytest" in sys_lower or "test generation" in sys_lower:
        return _TEST_GEN_RESPONSE
    if "risk" in sys_lower:
        return _RISK_RESPONSE
    if "project documentation" in user_lower:
        return _DOC_RESPONSE
    if "generate a regression test" in user_lower:
        return _TEST_GEN_RESPONSE
    if "test files" in user_lower:
        return _TEST_RESPONSE
    if "blast radius" in user_lower or "risk" in user_lower:
        return _RISK_RESPONSE

    return json.dumps({"result": "Demo mode — set GEMINI_API_KEY for live AI analysis."})

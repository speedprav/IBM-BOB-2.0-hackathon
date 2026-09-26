"""
LLM client — uses Google Gemini free tier via google-generativeai SDK.
Get a free API key at: https://aistudio.google.com/app/apikey
Set environment variable: GEMINI_API_KEY=your_key_here

If no key is set, the client falls back to DEMO MODE which returns
pre-computed realistic results for the Demo Orders scenario.
"""
from __future__ import annotations
import os

# Model names for google-generativeai SDK
_GEMINI_MODELS = [
    "gemini-1.5-flash",        # cheapest, free tier
    "gemini-1.5-flash-latest", # fallback
    "gemini-1.5-pro",          # fallback
]
_GEMINI_MODEL = _GEMINI_MODELS[0]

# ── Demo-mode flag ────────────────────────────────────────────────────────────
def _has_key() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def complete(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2048,
    model: str = _GEMINI_MODEL,
) -> str:
    """
    Single-turn completion.
    Uses Gemini free tier when GEMINI_API_KEY is set.
    Falls back to realistic demo responses otherwise.
    """
    if _has_key():
        return _gemini_complete(system_prompt, user_prompt, max_tokens, model)
    else:
        return _demo_complete(system_prompt, user_prompt)


# ── Gemini implementation (google-generativeai SDK) ───────────────────────────
def _gemini_complete(system_prompt: str, user_prompt: str, max_tokens: int, model: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        return _demo_complete(system_prompt, user_prompt)

    import time
    key = os.environ["GEMINI_API_KEY"].strip()
    genai.configure(api_key=key)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    models_to_try = [model] + [m for m in _GEMINI_MODELS if m != model]
    last_err = None
    for attempt_model in models_to_try:
        try:
            m = genai.GenerativeModel(
                model_name=attempt_model,
                generation_config={"max_output_tokens": max_tokens},
            )
            response = m.generate_content(full_prompt)
            return response.text
        except Exception as e:
            err_str = str(e)
            if any(x in err_str for x in ("503", "UNAVAILABLE", "404", "NOT_FOUND", "429", "RESOURCE_EXHAUSTED")):
                last_err = e
                time.sleep(1)
                continue
            raise
    raise last_err  # type: ignore


# ── Demo fallback — realistic pre-computed results ───────────────────────────
import json

_RISK_RESPONSE = json.dumps([
    {
        "severity": "high",
        "category": "regression",
        "title": "test_cannot_update_confirmed_order will break",
        "description": "The existing test explicitly asserts that updating a confirmed order raises OrderValidationError. The change removes this guard, so the test will fail.",
        "why_it_matters": "A failing test signals that the contract between the service layer and the rest of the system has changed. Merging with a broken test masks the regression.",
        "affected_location": "tests/test_orders.py:TestUpdateOrder.test_cannot_update_confirmed_order",
        "evidence": "Old code: `if not order.can_be_updated()` → raises on CONFIRMED. New code: allows PENDING and CONFIRMED, silently expanding the update window.",
        "suggested_mitigation": "Update or remove the test after explicitly deciding whether confirmed-order updates are intentional, and communicate the contract change to API consumers."
    },
    {
        "severity": "high",
        "category": "api_contract",
        "title": "PATCH /orders/<id> now accepts confirmed orders — undocumented API contract change",
        "description": "External callers currently expect PATCH to return 422 for confirmed orders. This change silently alters that behavior without a version bump.",
        "why_it_matters": "API consumers (mobile apps, partner integrations) may depend on the 422 response to show 'order locked' UI. Silent behavior change can cause data corruption on the client side.",
        "affected_location": "api/routes.py:update_order",
        "evidence": "routes.py delegates entirely to order_service.update_order. The status check was the only guard; it is now relaxed without a changelogs entry.",
        "suggested_mitigation": "Add a CHANGELOG entry, bump the API minor version, and document the new accepted statuses in the API spec."
    },
    {
        "severity": "critical",
        "category": "security",
        "title": "Discount manipulation window extended to confirmed orders",
        "description": "Admins can apply discounts during update. By allowing confirmed-order updates, a malicious or mistaken admin can apply a retroactive discount after the customer has already accepted the confirmed price.",
        "why_it_matters": "Financial integrity risk: an order can be discounted after confirmation, bypassing the pricing approval workflow that only applies at creation/pending stage.",
        "affected_location": "services/order_service.py:update_order + auth.py:can_apply_discount",
        "evidence": "`can_apply_discount` returns True for ADMIN unconditionally. The status gate was the only control preventing post-confirmation discount injection.",
        "suggested_mitigation": "Add an explicit guard: disallow discount changes on orders that are not in PENDING status, separate from the general update permission."
    },
    {
        "severity": "medium",
        "category": "data",
        "title": "Order items can be replaced after warehouse has committed inventory",
        "description": "Confirmed orders typically mean the warehouse has reserved or picked items. Allowing item replacement at CONFIRMED status can create inventory inconsistencies.",
        "why_it_matters": "Inventory reservations made at confirmation time will be orphaned if items are swapped post-confirmation.",
        "affected_location": "services/order_service.py:update_order (items replacement branch)",
        "evidence": "No inventory integration exists in this codebase, but the architecture doc states confirmed orders should be treated as warehouse-committed.",
        "suggested_mitigation": "If item updates on confirmed orders are required, add an inventory release/re-reserve step or restrict updates to notes-only for confirmed orders."
    }
])

_TEST_RESPONSE = json.dumps({
    "affected_tests": [
        {
            "test_file": "tests/test_orders.py",
            "test_name": "TestUpdateOrder.test_cannot_update_confirmed_order",
            "relevance": "directly_affected",
            "will_break": True,
            "reason": "This test explicitly asserts that updating a CONFIRMED order raises OrderValidationError. The change removes that guard, so the assertion will fail."
        },
        {
            "test_file": "tests/test_orders.py",
            "test_name": "TestUpdateOrder.test_customer_can_update_own_pending_order",
            "relevance": "related",
            "will_break": False,
            "reason": "Still tests PENDING update path which is unchanged, but should be reviewed alongside the new CONFIRMED path."
        },
        {
            "test_file": "tests/test_orders.py",
            "test_name": "TestUpdateOrder.test_admin_can_apply_discount",
            "relevance": "related",
            "will_break": False,
            "reason": "Discount logic is unchanged but now reachable on CONFIRMED orders — a new risk scenario not covered by this test."
        }
    ],
    "coverage_gaps": [
        "No test covers updating an order in CONFIRMED status (the new allowed path)",
        "No test verifies a customer cannot apply a discount to a confirmed order",
        "No test checks that item replacement on a confirmed order updates the total correctly",
        "No test verifies the API returns the correct HTTP status for confirmed-order updates",
        "No regression test for admin applying a retroactive discount to a confirmed order"
    ]
})

_DOC_RESPONSE = json.dumps([
    "The architecture doc states: only PENDING orders can be updated (item/notes changes).",
    "Status transitions must follow the defined lifecycle: PENDING → CONFIRMED → SHIPPED → DELIVERED.",
    "Once shipped, no modifications or cancellations are allowed.",
    "Only admins can apply discounts — discount is applied at update time and persists on the order.",
    "Customers can only modify their own orders; admins and support can modify any order."
])

_TEST_GEN_RESPONSE = '''\
"""
Regression tests for: Allow customers to update orders in CONFIRMED status.

These tests cover the risk scenarios identified by DevTwin analysis:
- API contract change for confirmed-order updates
- Discount manipulation on confirmed orders
- Existing broken test documentation
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from models import User, UserRole, OrderItem, OrderStatus, UpdateOrderRequest
from services.order_service import OrderService, OrderValidationError
from auth import PermissionError
from repositories.order_repository import OrderRepository


def make_service():
    repo = OrderRepository()
    return OrderService(repo), repo


def customer(uid="u1"):
    return User(id=uid, email=f"{uid}@example.com", role=UserRole.CUSTOMER)


def admin():
    return User(id="admin1", email="admin@example.com", role=UserRole.ADMIN)


def items():
    return [OrderItem("p1", "Widget", 2, 9.99)]


class TestConfirmedOrderUpdateRegression:
    """Regression suite for the confirmed-order update change."""

    def test_confirmed_order_can_now_be_updated_notes(self):
        """After the change: updating notes on a confirmed order should succeed."""
        svc, repo = make_service()
        order = svc.create_order(customer(), items())
        order.status = OrderStatus.CONFIRMED
        repo.save(order)
        updated = svc.update_order(customer(), order.id, UpdateOrderRequest(notes="urgent"))
        assert updated.notes == "urgent"

    def test_confirmed_order_item_replacement(self):
        """After the change: item replacement on a confirmed order should reflect in total."""
        svc, repo = make_service()
        order = svc.create_order(customer(), items())
        order.status = OrderStatus.CONFIRMED
        repo.save(order)
        new_items = [OrderItem("p2", "Gadget", 1, 49.99)]
        updated = svc.update_order(customer(), order.id, UpdateOrderRequest(items=new_items))
        assert updated.total == pytest.approx(49.99)

    def test_admin_cannot_apply_retroactive_discount_to_confirmed_order(self):
        """SECURITY RISK: Admin applying a discount to a confirmed order."""
        svc, repo = make_service()
        order = svc.create_order(customer(), items())
        original_total = order.total
        order.status = OrderStatus.CONFIRMED
        repo.save(order)
        updated = svc.update_order(admin(), order.id, UpdateOrderRequest(discount_percent=50.0))
        assert updated.discount_percent == 50.0
        assert updated.total < original_total

    def test_customer_still_cannot_update_other_users_confirmed_order(self):
        """Auth guard should still prevent cross-customer updates."""
        svc, repo = make_service()
        owner = customer("owner")
        stranger = customer("stranger")
        order = svc.create_order(owner, items())
        order.status = OrderStatus.CONFIRMED
        repo.save(order)
        with pytest.raises(PermissionError):
            svc.update_order(stranger, order.id, UpdateOrderRequest(notes="hack"))

    def test_shipped_order_still_cannot_be_updated(self):
        """The change should not affect SHIPPED orders — they must remain immutable."""
        svc, repo = make_service()
        order = svc.create_order(customer(), items())
        order.status = OrderStatus.SHIPPED
        repo.save(order)
        with pytest.raises(OrderValidationError):
            svc.update_order(customer(), order.id, UpdateOrderRequest(notes="too late"))
'''


def _demo_complete(system_prompt: str, user_prompt: str) -> str:
    """Return realistic pre-computed responses based on which agent is calling."""
    prompt_lower = (system_prompt + user_prompt).lower()

    if "risk" in prompt_lower and "json array" in prompt_lower:
        return _RISK_RESPONSE

    if "test engineer" in prompt_lower and "affected_tests" in prompt_lower:
        return _TEST_RESPONSE

    if "documentation analyst" in prompt_lower or "architectural invariants" in prompt_lower:
        return _DOC_RESPONSE

    if "regression test" in prompt_lower or "pytest regression" in prompt_lower:
        return _TEST_GEN_RESPONSE

    # Generic fallback
    return json.dumps({"result": "Demo mode — set GEMINI_API_KEY for live AI analysis."})

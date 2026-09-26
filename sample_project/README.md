# Demo Orders

A sample e-commerce order management service used as the target project for DevTwin analysis demonstrations.

## Architecture

```
api/routes.py          ← Flask HTTP handlers
services/order_service.py  ← Business logic, validation, authorization
repositories/order_repository.py  ← Data access layer
auth.py                ← Token authentication, permission checks
models.py              ← Domain models (Order, User, OrderItem, etc.)
tests/                 ← Pytest test suite
```

## Running Tests

```bash
cd sample_project
pip install pytest flask
pytest tests/ -v
```

## Prepared Demo Change

The change file `demo_change.diff` contains a realistic-looking but consequential modification:

**Change:** Allow customers to update orders in `CONFIRMED` status (not just `PENDING`).

**Hidden consequences:**
- Authorization bypass: `can_modify_order` is now callable on confirmed orders by any customer
- Discount application risk: confirmed orders with discounts can be retroactively modified
- API contract violation: the PATCH endpoint now behaves differently for confirmed orders
- Existing tests that assert `cannot_update_confirmed_order` will break
- Status transition integrity is compromised

This is the kind of change DevTwin is designed to surface before merge.

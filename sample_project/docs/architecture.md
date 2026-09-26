# Demo Orders Architecture

## Component Overview

### API Layer (`api/routes.py`)
- Flask HTTP endpoints
- Handles authentication token extraction
- Delegates all business logic to OrderService
- Error handlers convert domain exceptions to HTTP responses

### Service Layer (`services/order_service.py`)
- Core business logic
- Order lifecycle management
- Authorization delegation to `auth.py`
- Validation rules enforced here

### Repository Layer (`repositories/order_repository.py`)
- Data access abstraction
- In-memory storage (replaceable with DB)
- No business logic

### Auth Module (`auth.py`)
- Token-based authentication
- Role-based permission checks
- `can_modify_order`: ownership + role check
- `can_apply_discount`: admin-only gate

### Models (`models.py`)
- `Order.can_be_updated()`: status gate → PENDING only
- `Order.can_be_cancelled()`: status gate → PENDING | CONFIRMED

## Key Invariants

1. Customers can only modify their own orders
2. Only PENDING orders can be updated (item/notes changes)
3. Only PENDING and CONFIRMED orders can be cancelled
4. Only admins can apply discounts
5. Discount is applied at update time and persists on the order

## Status Transitions

```
PENDING → CONFIRMED → SHIPPED → DELIVERED
       ↓           ↓
   CANCELLED   CANCELLED
```

Once shipped, no modifications or cancellations are allowed.

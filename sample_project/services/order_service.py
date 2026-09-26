"""
Order service — business logic layer.
"""
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from typing import List, Optional

from models import Order, OrderItem, OrderStatus, UpdateOrderRequest, User
from auth import can_modify_order, can_apply_discount, PermissionError
from repositories.order_repository import OrderRepository, OrderNotFoundError


class OrderValidationError(Exception):
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class OrderService:

    def __init__(self, repository: OrderRepository) -> None:
        self._repo = repository

    def create_order(self, user: User, items: List[OrderItem]) -> Order:
        if not items:
            raise OrderValidationError("Order must contain at least one item", field="items")
        for item in items:
            if item.quantity <= 0:
                raise OrderValidationError(
                    f"Item quantity must be positive: {item.product_id}", field="quantity"
                )
            if item.unit_price < 0:
                raise OrderValidationError(
                    f"Item price cannot be negative: {item.product_id}", field="unit_price"
                )

        order = Order(
            id=self._generate_id(),
            user_id=user.id,
            items=items,
            status=OrderStatus.PENDING,
        )
        return self._repo.save(order)

    def update_order(self, user: User, order_id: str, request: UpdateOrderRequest) -> Order:
        order = self._repo.get(order_id)

        if not can_modify_order(user, order):
            raise PermissionError("You do not have permission to modify this order")

        if not order.can_be_updated():
            raise OrderValidationError(
                f"Order in status '{order.status.value}' cannot be updated"
            )

        if request.items is not None:
            if not request.items:
                raise OrderValidationError("Updated order must contain at least one item", field="items")
            order.items = request.items

        if request.discount_percent is not None:
            if not can_apply_discount(user):
                raise PermissionError("Only admins can apply discounts")
            if not (0 <= request.discount_percent <= 100):
                raise OrderValidationError("Discount must be between 0 and 100", field="discount_percent")
            order.discount_percent = request.discount_percent

        if request.notes is not None:
            order.notes = request.notes

        if request.status is not None:
            order.status = request.status

        order.updated_at = _now()
        return self._repo.save(order)

    def cancel_order(self, user: User, order_id: str) -> Order:
        order = self._repo.get(order_id)

        if not can_modify_order(user, order):
            raise PermissionError("You do not have permission to cancel this order")

        if not order.can_be_cancelled():
            raise OrderValidationError(
                f"Order in status '{order.status.value}' cannot be cancelled"
            )

        order.status = OrderStatus.CANCELLED
        order.updated_at = _now()
        return self._repo.save(order)

    def get_order(self, user: User, order_id: str) -> Order:
        order = self._repo.get(order_id)
        if not can_modify_order(user, order):
            raise PermissionError("You do not have access to this order")
        return order

    def list_orders(self, user: User) -> List[Order]:
        from models import UserRole
        if user.role in (UserRole.ADMIN, UserRole.SUPPORT):
            return list(self._repo._store.values())
        return self._repo.list_by_user(user.id)

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return str(uuid.uuid4())

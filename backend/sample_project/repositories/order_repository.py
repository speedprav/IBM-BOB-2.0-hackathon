"""
Order repository — data access layer.
"""
from typing import Dict, List, Optional
from models import Order, OrderStatus


class OrderNotFoundError(Exception):
    def __init__(self, order_id: str):
        self.order_id = order_id
        super().__init__(f"Order not found: {order_id}")


class OrderRepository:
    """In-memory order store (swap for a real DB in production)."""

    def __init__(self) -> None:
        self._store: Dict[str, Order] = {}

    def save(self, order: Order) -> Order:
        self._store[order.id] = order
        return order

    def get(self, order_id: str) -> Order:
        order = self._store.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    def list_by_user(self, user_id: str) -> List[Order]:
        return [o for o in self._store.values() if o.user_id == user_id]

    def list_by_status(self, status: OrderStatus) -> List[Order]:
        return [o for o in self._store.values() if o.status == status]

    def delete(self, order_id: str) -> None:
        if order_id not in self._store:
            raise OrderNotFoundError(order_id)
        del self._store[order_id]

    def count(self) -> int:
        return len(self._store)

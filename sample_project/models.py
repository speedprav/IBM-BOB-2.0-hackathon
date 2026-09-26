"""
Domain models for the Demo Orders project.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from enum import Enum
from typing import List, Optional


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class UserRole(Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPPORT = "support"


@dataclass
class User:
    id: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=_now)


@dataclass
class OrderItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    id: str
    user_id: str
    items: List[OrderItem]
    status: OrderStatus
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    discount_percent: float = 0.0
    notes: Optional[str] = None

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal * (1 - self.discount_percent / 100)

    def can_be_cancelled(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED)

    def can_be_updated(self) -> bool:
        """Only pending orders can be updated by customers."""
        return self.status == OrderStatus.PENDING


@dataclass
class UpdateOrderRequest:
    items: Optional[List[OrderItem]] = None
    discount_percent: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[OrderStatus] = None

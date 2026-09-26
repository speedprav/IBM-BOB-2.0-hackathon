"""
Tests for order service business logic.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from models import User, UserRole, OrderItem, OrderStatus, UpdateOrderRequest
from services.order_service import OrderService, OrderValidationError
from auth import PermissionError, register_user
from repositories.order_repository import OrderRepository, OrderNotFoundError


def make_repo_and_service():
    repo = OrderRepository()
    service = OrderService(repo)
    return repo, service


def make_customer(user_id: str = "u1") -> User:
    return User(id=user_id, email=f"{user_id}@example.com", role=UserRole.CUSTOMER)


def make_admin(user_id: str = "admin1") -> User:
    return User(id=user_id, email="admin@example.com", role=UserRole.ADMIN)


def make_items():
    return [OrderItem(product_id="p1", product_name="Widget", quantity=2, unit_price=9.99)]


class TestCreateOrder:
    def test_creates_pending_order(self):
        _, service = make_repo_and_service()
        customer = make_customer()
        order = service.create_order(customer, make_items())
        assert order.status == OrderStatus.PENDING
        assert order.user_id == "u1"

    def test_raises_on_empty_items(self):
        _, service = make_repo_and_service()
        with pytest.raises(OrderValidationError):
            service.create_order(make_customer(), [])

    def test_raises_on_negative_quantity(self):
        _, service = make_repo_and_service()
        items = [OrderItem("p1", "Widget", -1, 10.0)]
        with pytest.raises(OrderValidationError):
            service.create_order(make_customer(), items)

    def test_raises_on_negative_price(self):
        _, service = make_repo_and_service()
        items = [OrderItem("p1", "Widget", 1, -5.0)]
        with pytest.raises(OrderValidationError):
            service.create_order(make_customer(), items)


class TestUpdateOrder:
    def test_customer_can_update_own_pending_order(self):
        _, service = make_repo_and_service()
        customer = make_customer()
        order = service.create_order(customer, make_items())
        new_items = [OrderItem("p2", "Gadget", 1, 19.99)]
        updated = service.update_order(customer, order.id, UpdateOrderRequest(items=new_items))
        assert updated.items[0].product_id == "p2"

    def test_customer_cannot_update_others_order(self):
        _, service = make_repo_and_service()
        owner = make_customer("owner")
        stranger = make_customer("stranger")
        order = service.create_order(owner, make_items())
        with pytest.raises(PermissionError):
            service.update_order(stranger, order.id, UpdateOrderRequest(notes="hi"))

    def test_cannot_update_confirmed_order(self):
        repo, service = make_repo_and_service()
        customer = make_customer()
        order = service.create_order(customer, make_items())
        # Manually advance status
        order.status = OrderStatus.CONFIRMED
        repo.save(order)
        with pytest.raises(OrderValidationError):
            service.update_order(customer, order.id, UpdateOrderRequest(notes="too late"))

    def test_admin_can_apply_discount(self):
        _, service = make_repo_and_service()
        customer = make_customer()
        admin = make_admin()
        order = service.create_order(customer, make_items())
        updated = service.update_order(admin, order.id, UpdateOrderRequest(discount_percent=10.0))
        assert updated.discount_percent == 10.0

    def test_customer_cannot_apply_discount(self):
        _, service = make_repo_and_service()
        customer = make_customer()
        order = service.create_order(customer, make_items())
        with pytest.raises(PermissionError):
            service.update_order(customer, order.id, UpdateOrderRequest(discount_percent=10.0))


class TestCancelOrder:
    def test_can_cancel_pending_order(self):
        _, service = make_repo_and_service()
        customer = make_customer()
        order = service.create_order(customer, make_items())
        cancelled = service.cancel_order(customer, order.id)
        assert cancelled.status == OrderStatus.CANCELLED

    def test_cannot_cancel_shipped_order(self):
        repo, service = make_repo_and_service()
        customer = make_customer()
        order = service.create_order(customer, make_items())
        order.status = OrderStatus.SHIPPED
        repo.save(order)
        with pytest.raises(OrderValidationError):
            service.cancel_order(customer, order.id)

"""
Tests for authentication and authorization utilities.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from models import User, UserRole, Order, OrderStatus, OrderItem
from auth import (
    get_current_user, register_user, require_role,
    can_modify_order, can_apply_discount, AuthError, PermissionError
)


def make_order(user_id: str = "u1") -> Order:
    return Order(
        id="ord1",
        user_id=user_id,
        items=[OrderItem("p1", "Widget", 1, 10.0)],
        status=OrderStatus.PENDING,
    )


class TestTokenAuth:
    def test_valid_token_returns_user(self):
        user = User(id="u100", email="test@example.com", role=UserRole.CUSTOMER)
        register_user(user, "valid_token_100")
        result = get_current_user("valid_token_100")
        assert result.id == "u100"

    def test_invalid_token_raises_auth_error(self):
        with pytest.raises(AuthError) as exc_info:
            get_current_user("nonexistent_token_xyz")
        assert exc_info.value.code == "INVALID_TOKEN"

    def test_inactive_user_raises_auth_error(self):
        user = User(id="u101", email="inactive@example.com", role=UserRole.CUSTOMER, is_active=False)
        register_user(user, "inactive_token_101")
        with pytest.raises(AuthError) as exc_info:
            get_current_user("inactive_token_101")
        assert exc_info.value.code == "ACCOUNT_INACTIVE"


class TestRequireRole:
    def test_matching_role_passes(self):
        admin = User(id="a1", email="admin@example.com", role=UserRole.ADMIN)
        require_role(admin, UserRole.ADMIN)  # should not raise

    def test_non_matching_role_raises(self):
        customer = User(id="c1", email="c@example.com", role=UserRole.CUSTOMER)
        with pytest.raises(PermissionError):
            require_role(customer, UserRole.ADMIN)

    def test_multiple_acceptable_roles(self):
        support = User(id="s1", email="s@example.com", role=UserRole.SUPPORT)
        require_role(support, UserRole.ADMIN, UserRole.SUPPORT)  # should not raise


class TestCanModifyOrder:
    def test_owner_customer_can_modify(self):
        customer = User(id="u1", email="c@example.com", role=UserRole.CUSTOMER)
        order = make_order(user_id="u1")
        assert can_modify_order(customer, order) is True

    def test_non_owner_customer_cannot_modify(self):
        stranger = User(id="u2", email="other@example.com", role=UserRole.CUSTOMER)
        order = make_order(user_id="u1")
        assert can_modify_order(stranger, order) is False

    def test_admin_can_modify_any_order(self):
        admin = User(id="admin", email="admin@example.com", role=UserRole.ADMIN)
        order = make_order(user_id="some_customer")
        assert can_modify_order(admin, order) is True

    def test_support_can_modify_any_order(self):
        support = User(id="sup1", email="sup@example.com", role=UserRole.SUPPORT)
        order = make_order(user_id="some_customer")
        assert can_modify_order(support, order) is True


class TestCanApplyDiscount:
    def test_admin_can_apply_discount(self):
        admin = User(id="a1", email="admin@example.com", role=UserRole.ADMIN)
        assert can_apply_discount(admin) is True

    def test_customer_cannot_apply_discount(self):
        customer = User(id="c1", email="c@example.com", role=UserRole.CUSTOMER)
        assert can_apply_discount(customer) is False

    def test_support_cannot_apply_discount(self):
        support = User(id="s1", email="s@example.com", role=UserRole.SUPPORT)
        assert can_apply_discount(support) is False

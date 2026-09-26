"""
Authentication and authorization utilities.
"""
from typing import Optional
from models import User, UserRole, Order


class AuthError(Exception):
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class PermissionError(Exception):
    def __init__(self, message: str, required_role: Optional[UserRole] = None):
        self.message = message
        self.required_role = required_role
        super().__init__(message)


# Simulated token store (in production, use JWT or session store)
_active_tokens: dict[str, str] = {}  # token -> user_id
_users: dict[str, User] = {}         # user_id -> User


def register_user(user: User, token: str) -> None:
    """Register a user and their session token."""
    _users[user.id] = user
    _active_tokens[token] = user.id


def get_current_user(token: str) -> User:
    """Resolve a token to a User, raising AuthError if invalid."""
    user_id = _active_tokens.get(token)
    if not user_id:
        raise AuthError("Invalid or expired token", code="INVALID_TOKEN")
    user = _users.get(user_id)
    if not user:
        raise AuthError("User not found", code="USER_NOT_FOUND")
    if not user.is_active:
        raise AuthError("Account is deactivated", code="ACCOUNT_INACTIVE")
    return user


def require_role(user: User, *roles: UserRole) -> None:
    """Assert that the user holds at least one of the given roles."""
    if user.role not in roles:
        raise PermissionError(
            f"Action requires one of: {[r.value for r in roles]}",
            required_role=roles[0] if roles else None,
        )


def can_modify_order(user: User, order: Order) -> bool:
    """
    Determine if the user can modify an order.
    Admins and support can always modify.
    Customers can only modify their own orders.
    """
    if user.role in (UserRole.ADMIN, UserRole.SUPPORT):
        return True
    return order.user_id == user.id


def can_apply_discount(user: User) -> bool:
    """Only admins can apply discounts."""
    return user.role == UserRole.ADMIN

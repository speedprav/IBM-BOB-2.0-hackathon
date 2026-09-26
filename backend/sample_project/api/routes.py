"""
Flask API routes for the Demo Orders service.
"""
from flask import Flask, jsonify, request, abort
from models import OrderItem, OrderStatus, UpdateOrderRequest
from services.order_service import OrderService, OrderValidationError
from auth import get_current_user, AuthError, PermissionError
from repositories.order_repository import OrderRepository, OrderNotFoundError

app = Flask(__name__)
_repo = OrderRepository()
_service = OrderService(_repo)


def _get_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Missing or malformed Authorization header")
    return auth_header[7:]


@app.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify({"error": e.message, "code": e.code}), 401


@app.errorhandler(PermissionError)
def handle_permission_error(e):
    return jsonify({"error": e.message}), 403


@app.errorhandler(OrderNotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404


@app.errorhandler(OrderValidationError)
def handle_validation_error(e):
    body = {"error": str(e)}
    if e.field:
        body["field"] = e.field
    return jsonify(body), 422


@app.route("/orders", methods=["GET"])
def list_orders():
    user = get_current_user(_get_token())
    orders = _service.list_orders(user)
    return jsonify([_serialize_order(o) for o in orders])


@app.route("/orders", methods=["POST"])
def create_order():
    user = get_current_user(_get_token())
    data = request.get_json(force=True)
    items = [
        OrderItem(
            product_id=i["product_id"],
            product_name=i["product_name"],
            quantity=i["quantity"],
            unit_price=i["unit_price"],
        )
        for i in data.get("items", [])
    ]
    order = _service.create_order(user, items)
    return jsonify(_serialize_order(order)), 201


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    user = get_current_user(_get_token())
    order = _service.get_order(user, order_id)
    return jsonify(_serialize_order(order))


@app.route("/orders/<order_id>", methods=["PATCH"])
def update_order(order_id: str):
    user = get_current_user(_get_token())
    data = request.get_json(force=True)

    req = UpdateOrderRequest(
        items=[
            OrderItem(
                product_id=i["product_id"],
                product_name=i["product_name"],
                quantity=i["quantity"],
                unit_price=i["unit_price"],
            )
            for i in data["items"]
        ] if "items" in data else None,
        discount_percent=data.get("discount_percent"),
        notes=data.get("notes"),
        status=OrderStatus(data["status"]) if "status" in data else None,
    )
    order = _service.update_order(user, order_id, req)
    return jsonify(_serialize_order(order))


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    user = get_current_user(_get_token())
    order = _service.cancel_order(user, order_id)
    return jsonify(_serialize_order(order))


def _serialize_order(order) -> dict:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status.value,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "subtotal": i.subtotal,
            }
            for i in order.items
        ],
        "subtotal": order.subtotal,
        "total": order.total,
        "discount_percent": order.discount_percent,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


if __name__ == "__main__":
    app.run(debug=True, port=5001)

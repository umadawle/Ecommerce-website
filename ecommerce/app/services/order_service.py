import math
from sqlalchemy.orm import Session
from typing import List
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderResponse, OrderListResponse, OrderTrackingResponse
from app.schemas.cart import CheckoutRequest
from app.core.exceptions import NotFoundError, BadRequestError, ForbiddenError
from app.services.cart_service import CartService


class OrderService:

    @staticmethod
    def _to_response(order: Order, items: List[OrderItem]) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            delivery_address=order.delivery_address,
            tracking_number=order.tracking_number,
            subtotal=order.subtotal,
            tax=order.tax,
            shipping_fee=order.shipping_fee,
            total_amount=order.total_amount,
            notes=order.notes,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    # ── Checkout (create order from cart) ────────────────────────────────────

    @staticmethod
    async def checkout(
        db: Session,
        cart_collection: AsyncIOMotorCollection,
        user_id: int,
        checkout_data: CheckoutRequest,
    ) -> OrderResponse:
        cart = await CartService.get_cart(cart_collection, user_id)
        if not cart.items:
            raise BadRequestError("Cart is empty")

        # Validate stock and build order items
        order_items_data = []
        subtotal = 0.0
        for cart_item in cart.items:
            product = db.query(Product).filter(
                Product.id == cart_item.product_id,
                Product.is_active == True,
            ).first()
            if not product:
                raise BadRequestError(f"Product '{cart_item.product_name}' is no longer available")
            if product.stock_quantity < cart_item.quantity:
                raise BadRequestError(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.stock_quantity}"
                )
            line_total = round(product.price * cart_item.quantity, 2)
            subtotal += line_total
            order_items_data.append({
                "product": product,
                "quantity": cart_item.quantity,
                "unit_price": product.price,
                "total_price": line_total,
            })

        tax = round(subtotal * 0.18, 2)          # 18% GST
        shipping_fee = 0.0 if subtotal >= 500 else 49.0
        total_amount = round(subtotal + tax + shipping_fee, 2)

        # Create order
        order = Order(
            user_id=user_id,
            delivery_address=checkout_data.delivery_address,
            subtotal=subtotal,
            tax=tax,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            notes=checkout_data.notes,
        )
        db.add(order)
        db.flush()  # get order.id

        # Create order items & decrement stock
        items = []
        for d in order_items_data:
            oi = OrderItem(
                order_id=order.id,
                product_id=d["product"].id,
                product_name=d["product"].name,
                quantity=d["quantity"],
                unit_price=d["unit_price"],
                total_price=d["total_price"],
            )
            db.add(oi)
            d["product"].stock_quantity -= d["quantity"]
            items.append(oi)

        db.commit()
        db.refresh(order)

        # Clear cart after successful order
        await CartService.clear_cart(cart_collection, user_id)

        return OrderService._to_response(order, items)

    # ── Read ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_order(db: Session, order_id: int, user_id: int) -> OrderResponse:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise NotFoundError("Order not found")
        if order.user_id != user_id:
            raise ForbiddenError("Access denied")
        items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        return OrderService._to_response(order, items)

    @staticmethod
    def get_order_history(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> OrderListResponse:
        query = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc())
        total = query.count()
        orders = query.offset((page - 1) * page_size).limit(page_size).all()
        responses = []
        for o in orders:
            items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
            responses.append(OrderService._to_response(o, items))
        return OrderListResponse(
            orders=responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Tracking ─────────────────────────────────────────────────────────────

    @staticmethod
    def track_order(db: Session, order_id: int, user_id: int) -> OrderTrackingResponse:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise NotFoundError("Order not found")
        if order.user_id != user_id:
            raise ForbiddenError("Access denied")

        # Simulated status history
        status_history = [
            {"status": "confirmed", "timestamp": str(order.created_at), "note": "Order placed"},
        ]
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            status_history.append({"status": "processing", "note": "Being prepared"})
        if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            status_history.append({"status": "shipped", "note": "Out for delivery"})
        if order.status == OrderStatus.DELIVERED:
            status_history.append({"status": "delivered", "note": "Delivered"})

        return OrderTrackingResponse(
            order_id=order.id,
            status=order.status,
            tracking_number=order.tracking_number,
            estimated_delivery="3-5 business days",
            status_history=status_history,
        )

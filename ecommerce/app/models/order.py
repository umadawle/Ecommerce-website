from sqlalchemy import (
    Column, Integer, String, Float, Text,
    DateTime, ForeignKey, Enum, func
)
import enum
from app.db.mysql import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    # Delivery
    delivery_address = Column(String(500), nullable=False)
    tracking_number = Column(String(100), nullable=True)

    # Totals
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    shipping_fee = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(255), nullable=False)  # snapshot at purchase time
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)           # snapshot at purchase time
    total_price = Column(Float, nullable=False)

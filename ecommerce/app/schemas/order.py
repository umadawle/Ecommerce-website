from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.order import OrderStatus


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    delivery_address: str
    tracking_number: Optional[str]
    subtotal: float
    tax: float
    shipping_fee: float
    total_amount: float
    notes: Optional[str]
    items: Optional[List[OrderItemResponse]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderTrackingResponse(BaseModel):
    order_id: int
    status: OrderStatus
    tracking_number: Optional[str]
    estimated_delivery: Optional[str] = None
    status_history: Optional[List[dict]] = None

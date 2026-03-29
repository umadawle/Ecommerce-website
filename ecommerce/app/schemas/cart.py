from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CartItem(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int = Field(..., ge=1)
    image_url: Optional[str] = None

    @property
    def total_price(self) -> float:
        return round(self.unit_price * self.quantity, 2)


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=1)


class CartResponse(BaseModel):
    user_id: int
    items: List[CartItem]
    subtotal: float
    item_count: int
    updated_at: Optional[datetime] = None


class CheckoutRequest(BaseModel):
    delivery_address: str = Field(..., min_length=10)
    payment_method: str                # matches PaymentMethod enum value
    notes: Optional[str] = None

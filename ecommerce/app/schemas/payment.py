from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentMethod, PaymentStatus


class InitiatePaymentRequest(BaseModel):
    order_id: int
    method: PaymentMethod
    # In a real system you'd pass tokenized card data, UPI VPA, etc.
    payment_token: Optional[str] = None   # Gateway token


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    method: PaymentMethod
    status: PaymentStatus
    amount: float
    currency: str
    transaction_id: Optional[str]
    receipt_number: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentReceiptResponse(BaseModel):
    receipt_number: str
    order_id: int
    amount: float
    currency: str
    method: PaymentMethod
    transaction_id: Optional[str]
    paid_at: datetime
    message: str = "Payment successful. Thank you for your purchase!"

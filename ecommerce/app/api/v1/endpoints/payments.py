from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.mysql import get_db
from app.models.user import User
from app.schemas.payment import (
    InitiatePaymentRequest, PaymentResponse, PaymentReceiptResponse,
)
from app.services.payment_service import PaymentService
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/payments", tags=["Payment"])


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate payment for an order",
)
def initiate_payment(
    request: InitiatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Processes payment for a confirmed order.

    **Supported methods:** `credit_card`, `debit_card`, `net_banking`, `upi`, `wallet`, `cod`

    In production this calls the actual payment gateway (e.g. Razorpay, Stripe).
    The stub always returns a successful transaction for demonstration.
    """
    return PaymentService.initiate_payment(db, current_user.id, request)


@router.get("/", response_model=List[PaymentResponse], summary="Get all payments by current user")
def get_my_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the full payment history for the authenticated user."""
    return PaymentService.get_user_payments(db, current_user.id)


@router.get(
    "/{payment_id}/receipt",
    response_model=PaymentReceiptResponse,
    summary="Download payment receipt",
)
def get_receipt(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a structured payment receipt for a successful transaction.
    Includes receipt number, transaction ID, amount, and method.
    """
    return PaymentService.get_receipt(db, payment_id, current_user.id)

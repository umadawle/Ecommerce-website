import uuid
from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order, OrderStatus
from app.schemas.payment import InitiatePaymentRequest, PaymentResponse, PaymentReceiptResponse
from app.core.exceptions import NotFoundError, ForbiddenError, PaymentError, BadRequestError


class PaymentService:

    @staticmethod
    def _generate_receipt_number() -> str:
        return f"RCPT-{uuid.uuid4().hex[:10].upper()}"

    @staticmethod
    def _generate_transaction_id() -> str:
        return f"TXN-{uuid.uuid4().hex.upper()}"

    # ── Initiate Payment ─────────────────────────────────────────────────────

    @staticmethod
    def initiate_payment(
        db: Session,
        user_id: int,
        request: InitiatePaymentRequest,
    ) -> PaymentResponse:
        order = db.query(Order).filter(Order.id == request.order_id).first()
        if not order:
            raise NotFoundError("Order not found")
        if order.user_id != user_id:
            raise ForbiddenError("Access denied")
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise BadRequestError("Order is not in a payable state")

        # Check for duplicate payment
        existing = db.query(Payment).filter(
            Payment.order_id == request.order_id,
            Payment.status == PaymentStatus.SUCCESS,
        ).first()
        if existing:
            raise BadRequestError("Order is already paid")

        # Simulate gateway call — always succeeds in this stub
        transaction_id = PaymentService._generate_transaction_id()
        receipt_number = PaymentService._generate_receipt_number()

        payment = Payment(
            order_id=order.id,
            user_id=user_id,
            method=request.method,
            status=PaymentStatus.SUCCESS,          # stub: real gateway returns async
            amount=order.total_amount,
            transaction_id=transaction_id,
            receipt_number=receipt_number,
            gateway_response="Payment processed successfully",
        )
        db.add(payment)

        # Update order status
        order.status = OrderStatus.CONFIRMED
        db.commit()
        db.refresh(payment)
        return PaymentResponse.model_validate(payment)

    # ── Get Receipt ──────────────────────────────────────────────────────────

    @staticmethod
    def get_receipt(db: Session, payment_id: int, user_id: int) -> PaymentReceiptResponse:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundError("Payment not found")
        if payment.user_id != user_id:
            raise ForbiddenError("Access denied")
        if payment.status != PaymentStatus.SUCCESS:
            raise BadRequestError("Payment was not successful")

        return PaymentReceiptResponse(
            receipt_number=payment.receipt_number,
            order_id=payment.order_id,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            transaction_id=payment.transaction_id,
            paid_at=payment.created_at,
        )

    # ── Payment History ──────────────────────────────────────────────────────

    @staticmethod
    def get_user_payments(db: Session, user_id: int) -> list[PaymentResponse]:
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .all()
        )
        return [PaymentResponse.model_validate(p) for p in payments]

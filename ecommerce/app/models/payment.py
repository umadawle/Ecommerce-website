from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, func
import enum
from app.db.mysql import Base


class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    NET_BANKING = "net_banking"
    UPI = "upi"
    WALLET = "wallet"
    COD = "cod"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")

    # Gateway reference
    transaction_id = Column(String(255), nullable=True, unique=True)
    gateway_response = Column(String(500), nullable=True)

    receipt_number = Column(String(100), nullable=True, unique=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

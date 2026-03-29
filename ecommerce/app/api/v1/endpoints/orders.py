from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.mysql import get_db
from app.models.user import User
from app.schemas.order import OrderResponse, OrderListResponse, OrderTrackingResponse
from app.services.order_service import OrderService
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Order Management"])


@router.get("/", response_model=OrderListResponse, summary="Get order history")
def get_order_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the authenticated user's paginated order history, newest first."""
    return OrderService.get_order_history(db, current_user.id, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order details")
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full details of a specific order including all line items.
    An order confirmation is effectively this response.
    """
    return OrderService.get_order(db, order_id, current_user.id)


@router.get("/{order_id}/track", response_model=OrderTrackingResponse, summary="Track order delivery")
def track_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the current delivery status and tracking number for an order."""
    return OrderService.track_order(db, order_id, current_user.id)

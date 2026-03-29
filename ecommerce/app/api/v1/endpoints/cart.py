from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.mysql import get_db
from app.db.mongo import get_cart_collection
from app.models.user import User
from app.models.product import Product
from app.schemas.cart import (
    CartResponse, AddToCartRequest,
    UpdateCartItemRequest, CheckoutRequest,
)
from app.schemas.order import OrderResponse
from app.services.cart_service import CartService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.api.v1.deps import get_current_user
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/cart", tags=["Cart & Checkout"])


@router.get("/", response_model=CartResponse, summary="View cart")
async def get_cart(current_user: User = Depends(get_current_user)):
    """Returns all items in the current user's cart with quantities and subtotal."""
    collection = get_cart_collection()
    return await CartService.get_cart(collection, current_user.id)


@router.post("/items", response_model=CartResponse, summary="Add item to cart")
async def add_to_cart(
    request: AddToCartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Adds a product to the cart. If the product already exists in the cart,
    the quantity is incremented.
    """
    product = db.query(Product).filter(
        Product.id == request.product_id, Product.is_active == True
    ).first()
    if not product:
        raise NotFoundError("Product not found")

    import json
    image_urls = []
    if product.image_urls:
        try:
            image_urls = json.loads(product.image_urls)
        except Exception:
            pass

    product_info = {
        "name": product.name,
        "price": product.price,
        "stock": product.stock_quantity,
        "image_url": image_urls[0] if image_urls else None,
    }
    collection = get_cart_collection()
    return await CartService.add_item(collection, current_user.id, request, product_info)


@router.patch("/items/{product_id}", response_model=CartResponse, summary="Update item quantity")
async def update_cart_item(
    product_id: int,
    request: UpdateCartItemRequest,
    current_user: User = Depends(get_current_user),
):
    """Updates the quantity of a specific item in the cart."""
    collection = get_cart_collection()
    return await CartService.update_item(collection, current_user.id, product_id, request)


@router.delete("/items/{product_id}", response_model=CartResponse, summary="Remove item from cart")
async def remove_cart_item(
    product_id: int,
    current_user: User = Depends(get_current_user),
):
    """Removes a specific product from the cart."""
    collection = get_cart_collection()
    return await CartService.remove_item(collection, current_user.id, product_id)


@router.delete("/", summary="Clear entire cart")
async def clear_cart(current_user: User = Depends(get_current_user)):
    """Empties the entire cart for the current user."""
    collection = get_cart_collection()
    return await CartService.clear_cart(collection, current_user.id)


@router.post("/checkout", response_model=OrderResponse, summary="Checkout – place an order")
async def checkout(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Converts the cart into a confirmed order.
    - Validates stock availability for every item.
    - Deducts stock quantities.
    - Calculates subtotal, 18% GST, and shipping fee.
    - Clears the cart upon success.
    """
    collection = get_cart_collection()
    return await OrderService.checkout(db, collection, current_user.id, checkout_data)

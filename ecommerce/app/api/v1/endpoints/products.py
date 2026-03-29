from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.mysql import get_db
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductListResponse, ProductSearchResponse,
)
from app.services.product_service import ProductService
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/products", tags=["Product Catalog"])


# ── Public routes (no auth required) ─────────────────────────────────────────

@router.get("/", response_model=ProductListResponse, summary="Browse products by category")
def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Browse all active products, optionally filtered by category."""
    return ProductService.list_products(db, category=category, page=page, page_size=page_size)


@router.get("/categories", response_model=list[str], summary="List all product categories")
def list_categories(db: Session = Depends(get_db)):
    """Returns all distinct product categories available in the catalog."""
    return ProductService.list_categories(db)


@router.get("/search", response_model=ProductSearchResponse, summary="Search products by keyword")
def search_products(
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Full-text search across product name, description, and category.
    In production, this is backed by Elasticsearch (per HLD).
    """
    return ProductService.search(db, keyword=q, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product details")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Returns full product details: images, description, specs, price, stock."""
    return ProductService.get_by_id(db, product_id)


# ── Admin routes (requires auth) ─────────────────────────────────────────────

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product (admin)",
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),   # auth check only
):
    """Add a new product to the catalog."""
    return ProductService.create(db, data)


@router.patch("/{product_id}", response_model=ProductResponse, summary="Update a product (admin)")
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update any product fields partially."""
    return ProductService.update(db, product_id, data)


@router.delete("/{product_id}", summary="Deactivate a product (admin)")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Soft-deletes (deactivates) a product so it no longer appears in browsing."""
    return ProductService.delete(db, product_id)

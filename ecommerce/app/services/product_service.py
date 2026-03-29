import json
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductListResponse, ProductSearchResponse
from app.core.exceptions import NotFoundError


class ProductService:

    @staticmethod
    def _serialize(product: Product) -> Product:
        """Parse JSON-stored fields back to Python objects."""
        if isinstance(product.image_urls, str):
            try:
                product.image_urls = json.loads(product.image_urls)
            except Exception:
                product.image_urls = []
        if isinstance(product.specifications, str):
            try:
                product.specifications = json.loads(product.specifications)
            except Exception:
                product.specifications = {}
        return product

    # ── CRUD ────────────────────────────────────────────────────────────────

    @staticmethod
    def create(db: Session, data: ProductCreate) -> Product:
        product = Product(
            name=data.name,
            description=data.description,
            specifications=json.dumps(data.specifications or {}),
            category=data.category,
            price=data.price,
            stock_quantity=data.stock_quantity,
            image_urls=json.dumps(data.image_urls or []),
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return ProductService._serialize(product)

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Product:
        product = db.query(Product).filter(
            Product.id == product_id, Product.is_active == True
        ).first()
        if not product:
            raise NotFoundError("Product not found")
        return ProductService._serialize(product)

    @staticmethod
    def update(db: Session, product_id: int, data: ProductUpdate) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError("Product not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ("specifications", "image_urls") and value is not None:
                value = json.dumps(value)
            setattr(product, field, value)
        db.commit()
        db.refresh(product)
        return ProductService._serialize(product)

    @staticmethod
    def delete(db: Session, product_id: int) -> dict:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError("Product not found")
        product.is_active = False
        db.commit()
        return {"message": "Product deactivated successfully"}

    # ── Browse / List ────────────────────────────────────────────────────────

    @staticmethod
    def list_products(
        db: Session,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProductListResponse:
        query = db.query(Product).filter(Product.is_active == True)
        if category:
            query = query.filter(Product.category == category)

        total = query.count()
        products = query.offset((page - 1) * page_size).limit(page_size).all()
        products = [ProductService._serialize(p) for p in products]

        import math
        return ProductListResponse(
            products=products,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    @staticmethod
    def list_categories(db: Session) -> List[str]:
        rows = (
            db.query(Product.category)
            .filter(Product.is_active == True)
            .distinct()
            .all()
        )
        return [r[0] for r in rows]

    # ── Search ───────────────────────────────────────────────────────────────

    @staticmethod
    def search(db: Session, keyword: str, page: int = 1, page_size: int = 20) -> ProductSearchResponse:
        query = db.query(Product).filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(f"%{keyword}%"),
                Product.description.ilike(f"%{keyword}%"),
                Product.category.ilike(f"%{keyword}%"),
            ),
        )
        total = query.count()
        products = query.offset((page - 1) * page_size).limit(page_size).all()
        products = [ProductService._serialize(p) for p in products]
        return ProductSearchResponse(query=keyword, products=products, total=total)

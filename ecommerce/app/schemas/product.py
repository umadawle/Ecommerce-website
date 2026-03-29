from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    specifications: Optional[dict] = None
    category: str
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    image_urls: Optional[List[str]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    category: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    image_urls: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    specifications: Optional[dict]
    category: str
    price: float
    stock_quantity: int
    image_urls: Optional[List[str]]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductSearchResponse(BaseModel):
    query: str
    products: List[ProductResponse]
    total: int

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, func
from app.db.mysql import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    specifications = Column(Text, nullable=True)          # JSON string
    category = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    image_urls = Column(Text, nullable=True)              # JSON list of URLs
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

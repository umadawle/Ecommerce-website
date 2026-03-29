from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.schemas.cart import CartItem, CartResponse, AddToCartRequest, UpdateCartItemRequest
from app.core.exceptions import NotFoundError, BadRequestError


class CartService:

    @staticmethod
    def _compute_response(doc: dict) -> CartResponse:
        items = [CartItem(**i) for i in doc.get("items", [])]
        subtotal = round(sum(i.unit_price * i.quantity for i in items), 2)
        return CartResponse(
            user_id=doc["user_id"],
            items=items,
            subtotal=subtotal,
            item_count=sum(i.quantity for i in items),
            updated_at=doc.get("updated_at"),
        )

    @staticmethod
    async def get_cart(collection: AsyncIOMotorCollection, user_id: int) -> CartResponse:
        doc = await collection.find_one({"user_id": user_id})
        if not doc:
            return CartResponse(user_id=user_id, items=[], subtotal=0.0, item_count=0)
        return CartService._compute_response(doc)

    @staticmethod
    async def add_item(
        collection: AsyncIOMotorCollection,
        user_id: int,
        request: AddToCartRequest,
        product_info: dict,            # {"name", "price", "image_url", "stock"}
    ) -> CartResponse:
        if product_info["stock"] < request.quantity:
            raise BadRequestError(f"Only {product_info['stock']} units available")

        doc = await collection.find_one({"user_id": user_id})

        if doc is None:
            # Create new cart
            new_item = {
                "product_id": request.product_id,
                "product_name": product_info["name"],
                "unit_price": product_info["price"],
                "quantity": request.quantity,
                "image_url": product_info.get("image_url"),
            }
            doc = {
                "user_id": user_id,
                "items": [new_item],
                "updated_at": datetime.now(timezone.utc),
            }
            await collection.insert_one(doc)
        else:
            items: list = doc.get("items", [])
            found = False
            for item in items:
                if item["product_id"] == request.product_id:
                    item["quantity"] += request.quantity
                    found = True
                    break
            if not found:
                items.append({
                    "product_id": request.product_id,
                    "product_name": product_info["name"],
                    "unit_price": product_info["price"],
                    "quantity": request.quantity,
                    "image_url": product_info.get("image_url"),
                })
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}},
            )

        updated_doc = await collection.find_one({"user_id": user_id})
        return CartService._compute_response(updated_doc)

    @staticmethod
    async def update_item(
        collection: AsyncIOMotorCollection,
        user_id: int,
        product_id: int,
        request: UpdateCartItemRequest,
    ) -> CartResponse:
        doc = await collection.find_one({"user_id": user_id})
        if not doc:
            raise NotFoundError("Cart not found")

        items: list = doc.get("items", [])
        found = False
        for item in items:
            if item["product_id"] == product_id:
                item["quantity"] = request.quantity
                found = True
                break
        if not found:
            raise NotFoundError("Item not found in cart")

        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}},
        )
        updated_doc = await collection.find_one({"user_id": user_id})
        return CartService._compute_response(updated_doc)

    @staticmethod
    async def remove_item(
        collection: AsyncIOMotorCollection,
        user_id: int,
        product_id: int,
    ) -> CartResponse:
        doc = await collection.find_one({"user_id": user_id})
        if not doc:
            raise NotFoundError("Cart not found")

        items = [i for i in doc.get("items", []) if i["product_id"] != product_id]
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}},
        )
        updated_doc = await collection.find_one({"user_id": user_id})
        return CartService._compute_response(updated_doc)

    @staticmethod
    async def clear_cart(collection: AsyncIOMotorCollection, user_id: int) -> dict:
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"items": [], "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        return {"message": "Cart cleared"}

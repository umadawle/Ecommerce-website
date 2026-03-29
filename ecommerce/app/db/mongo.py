from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

_client: AsyncIOMotorClient = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def get_cart_collection():
    """Returns the carts collection from MongoDB."""
    client = get_mongo_client()
    db = client[settings.MONGO_DB]
    return db["carts"]


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()
        _client = None

import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_client = MongoDB()

async def connect_to_mongo():
    # Use certifi for TLS CA certificates to fix SSL handshake errors
    db_client.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where()
    )
    db_client.db = db_client.client[settings.DATABASE_NAME]
    print(f"Connected to MongoDB: {settings.DATABASE_NAME}")

async def close_mongo_connection():
    if db_client.client:
        db_client.client.close()
        print("Closed MongoDB connection")

def get_database():
    return db_client.db

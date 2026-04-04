import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_client = MongoDB()

async def connect_to_mongo():
    # Use certifi for TLS CA certificates to fix SSL handshake errors
    # Added tlsAllowInvalidCertificates=True as a temporary bypass if certifi still fails locally
    db_client.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True, 
        connectTimeoutMS=10000, # 10s timeout for initial connection
        serverSelectionTimeoutMS=10000
    )
    
    # Verify the connection immediately on startup
    try:
        await db_client.client.admin.command('ping')
        db_client.db = db_client.client[settings.DATABASE_NAME]
        print(f"✅ Successfully connected to MongoDB: {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"❌ CRITICAL: MongoDB Connection Failed: {e}")
        print("TIP: Ensure your IP address is whitelisted in MongoDB Atlas (Network Access -> Add IP -> Allow Access from Anywhere)")
        # We don't raise an error here so the app can still start, 
        # but subsequent DB operations will fail as expected.

async def close_mongo_connection():
    if db_client.client:
        db_client.client.close()
        print("Closed MongoDB connection")

def get_database():
    return db_client.db

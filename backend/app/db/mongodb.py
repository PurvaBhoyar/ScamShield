import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_client = MongoDB()

async def connect_to_mongo():
    # Use certifi for TLS CA certificates to fix SSL handshake errors
    # Added tlsAllowInvalidCertificates=True and tlsInsecure=True as fallbacks
    try:
        db_client.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
            tlsInsecure=True # Final resort for SSL handshake issues, includes allowing invalid certs
        )
        
        # Verify the connection immediately on startup
        await db_client.client.admin.command('ping')
        db_client.db = db_client.client[settings.DATABASE_NAME]
        
        # ⚡ Caching optimization: Create an index on request_hash for fast lookups
        if db_client.db is not None:
            try:
                # Try creating unique index
                await db_client.db.scans.create_index("request_hash", unique=True)
            except Exception as index_err:
                # If it fails due to existing non-unique index, drop and recreate
                if "IndexKeySpecsConflict" in str(index_err) or "already exists" in str(index_err).lower():
                    print("Dropping legacy non-unique index for request_hash...")
                    await db_client.db.scans.drop_index("request_hash_1")
                    await db_client.db.scans.create_index("request_hash", unique=True)
                else:
                    print(f"Index creation warning: {index_err}")
            
        print(f"✅ Successfully connected to MongoDB: {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"❌ CRITICAL: MongoDB Connection Failed: {e}")
        # Try a more desperate connection string modification if it looks like a TLS issue
        if "SSL" in str(e) or "TLS" in str(e):
            print("Attempting connection with tlsInsecure=True fallback...")
            try:
                db_client.client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    tls=True,
                    tlsAllowInvalidCertificates=True,
                    serverSelectionTimeoutMS=5000
                )
                await db_client.client.admin.command('ping')
                db_client.db = db_client.client[settings.DATABASE_NAME]
                print("✅ Successfully connected to MongoDB (Insecure Mode)")
            except Exception as e2:
                print(f"❌ Still failed after fallback: {e2}")

async def close_mongo_connection():
    if db_client.client:
        db_client.client.close()
        print("Closed MongoDB connection")

def get_database():
    return db_client.db

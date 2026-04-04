import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_DETAILS = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.scamshield_db

async def seed_scam_templates():
    """
    Populates MongoDB with common scam patterns so the Vector Search 
    actually works for your live demo.
    """
    templates = [
        {
            "text": "Pay INR 500 for laptop security deposit. This is refundable after 3 months of joining. Send payment to UPI amz@ybl.",
            "scam_type": "Laptop Security Scam",
            "embedding": [] # To be filled by Atlas Vector Search if using Atlas
        },
        {
            "text": "Urgent hiring for Amazon. Salary 45000. No interview. Just pay processing fee of 999. Apply on telegram @amazonjobs_desk.",
            "scam_type": "Fee for Offer Scam",
            "embedding": []
        },
        {
            "text": "Government job alert! Earn 5000 per day by clicking links. No experience required. Send Aadhaar and PAN copy to proceed.",
            "scam_type": "Data Theft Scam",
            "embedding": []
        }
    ]
    
    # Insert templates (embeddings will be indexed by Atlas if configured)
    await db.scam_templates.delete_many({})
    await db.scam_templates.insert_many(templates)
    print("✅ Seeded 3 Scam Templates.")

async def seed_threat_intel():
    """
    Populates a blacklist of known scam identifiers.
    """
    intel = [
        {"identifier": "amz@ybl", "type": "upi", "severity": "critical", "source": "community_report"},
        {"identifier": "amazonjobs_desk", "type": "telegram", "severity": "high", "source": "platform_check"},
        {"identifier": "9876543210", "type": "phone", "severity": "critical", "source": "known_scammer"}
    ]
    await db.threat_intel.delete_many({})
    await db.threat_intel.insert_many(intel)
    print("✅ Seeded 3 Threat Intel Identifiers.")

async def main():
    await seed_scam_templates()
    await seed_threat_intel()

if __name__ == "__main__":
    asyncio.run(main())

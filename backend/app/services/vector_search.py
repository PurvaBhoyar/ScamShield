import os
import requests
from typing import List, Dict
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase

class VectorSearchService:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        if not settings.GOOGLE_API_KEY: return []
        try:
            # Use correct Google Embedding API format
            # Using v1beta for model support (some regions require it for 004)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GOOGLE_API_KEY}"
            payload = {
                "content": {
                    "role": "user",
                    "parts": [{"text": text}]
                },
                "task_type": "RETRIEVAL_QUERY"
            }
            response = requests.post(url, json=payload)
            if response.ok:
                data = response.json()
                return data.get("embedding", {}).get("values", [])
            else:
                print(f"Embedding Error: {response.status_code} {response.text[:200]}")
        except Exception as e:
            print(f"Embedding Error: {e}")
        return []

    @staticmethod
    async def find_similar_scams(db: AsyncIOMotorDatabase, text: str, threshold: float = 0.85) -> List[Dict]:
        findings = []
        embedding = await VectorSearchService.get_embedding(text)
        if not embedding: return findings
        pipeline = [{"$vectorSearch": {"index": "vector_index", "path": "embedding", "queryVector": embedding, "numCandidates": 100, "limit": 3}}, {"$project": {"text": 1, "score": {"$meta": "vectorSearchScore"}, "scam_type": 1}}, {"$match": {"score": {"$gte": threshold}}}]
        try:
            cursor = db.scam_templates.aggregate(pipeline)
            async for doc in cursor:
                findings.append({"type": "template_match", "severity": "high", "message": f"Found {int(doc['score'] * 100)}% match with known scam."})
        except Exception: pass
        return findings

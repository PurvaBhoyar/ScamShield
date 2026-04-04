import google.generativeai as genai
from typing import List, Dict
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase

class VectorSearchService:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        if not settings.GOOGLE_API_KEY: return []
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        result = genai.embed_content(model="models/text-embedding-004", content=text, task_type="retrieval_query")
        return result['embedding']

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

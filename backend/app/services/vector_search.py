import json
from groq import Groq
from typing import List, Dict
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase

class VectorSearchService:
    @staticmethod
    async def find_similar_scams(db: AsyncIOMotorDatabase, text: str, threshold: float = 0.85) -> List[Dict]:
        """
        Uses Groq's reasoning to identify if text matches known scam patterns
        in the database, replacing the need for a Google Embedding API.
        """
        findings = []
        
        if not settings.GROQ_API_KEY:
            print("⚠️ Warning: GROQ_API_KEY missing.")
            return findings

        if db is None:
            print("⚠️ Warning: Database not connected. Skipping Pattern Match.")
            return findings

        # 1. Fetch known scam categories from your MongoDB
        scam_templates = []
        try:
            # We fetch the scam_type and a sample text to give Groq context
            cursor = db.scam_templates.find({}, {"scam_type": 1, "text": 1})
            async for doc in cursor:
                scam_templates.append(f"- {doc['scam_type']}: {doc['text'][:200]}...")
        except Exception as e:
            print(f"❌ DB Fetch Error: {e}")
            return findings

        if not scam_templates:
            return findings

        # 2. Use Groq to perform Semantic Comparison
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        system_prompt = f"""
        You are a specialized Fraud Detection Agent. Compare the 'User Text' against the 'Known Scam Patterns' provided.
        Identify if the User Text is a semantic match or a variation of these scams.
        
        KNOWN SCAM PATTERNS:
        {chr(10).join(scam_templates)}
        
        If a match is found, return a JSON object with:
        {{
            "match_found": true,
            "scam_type": "The category name",
            "confidence": 0-100,
            "reason": "Brief explanation of the similarity"
        }}
        If no match is found, return {{"match_found": false}}.
        """

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Text: {text[:5000]}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get("match_found") and result.get("confidence", 0) >= (threshold * 100):
                findings.append({
                    "type": "template_match",
                    "severity": "high",
                    "message": f"Semantic Match ({result['confidence']}%): Matches known '{result['scam_type']}' pattern. {result['reason']}"
                })
        except Exception as e:
            print(f"❌ Groq Semantic Match Error: {e}")
            
        return findings
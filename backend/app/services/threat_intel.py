import re
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

class ThreatIntelService:
    UPI_PATTERN = r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'
    PHONE_PATTERN = r'(?:\+91|0)?[6789]\d{9}'
    TELEGRAM_PATTERN = r'(?:t\.me/|@)([a-zA-Z0-9_]{5,32})'

    @staticmethod
    def extract_identifiers(text: str) -> Dict[str, List[str]]:
        return {
            "upi": list(set(re.findall(ThreatIntelService.UPI_PATTERN, text))),
            "phone": list(set(re.findall(ThreatIntelService.PHONE_PATTERN, text))),
            "telegram": list(set(re.findall(ThreatIntelService.TELEGRAM_PATTERN, text)))
        }

    @staticmethod
    async def check_blacklist(db: AsyncIOMotorDatabase, identifiers: Dict[str, List[str]]) -> List[Dict]:
        findings = []
        all_ids = identifiers["upi"] + identifiers["phone"] + identifiers["telegram"]
        if not all_ids: return findings
        cursor = db.threat_intel.find({"identifier": {"$in": all_ids}})
        async for entry in cursor:
            findings.append({
                "type": f"blacklisted_{entry['type']}",
                "severity": entry.get("severity", "high"),
                "message": f"Found blacklisted {entry['type']}: {entry['identifier']}"
            })
        return findings

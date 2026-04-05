import os
import json
from pathlib import Path
from typing import Dict, Any
from groq import Groq
from dotenv import load_dotenv

# --- 0. Precise Path Resolution ---
# Ensures the .env is found regardless of execution directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

# --- 1. Client Initialization with Sanitization ---
def _get_clean_key(key_name: str) -> str:
    """Strips hidden newline characters or whitespace from env variables."""
    raw_key = os.getenv(key_name, "").strip()
    if not raw_key:
        return ""
    # Filter out non-ASCII/control characters that break API calls
    return "".join(char for char in raw_key if 32 <= ord(char) <= 126).strip()

GROQ_API_KEY = _get_clean_key("GROQ_API_KEY")

# Initialize Groq Client exclusively
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- 2. Local Failsafe Engine ---
def _local_fallback_analysis(text: str) -> Dict[str, Any]:
    """Hard-coded keyword analysis if Groq API or network fails."""
    findings = []
    text_lower = text.lower()
    
    # Priority patterns based on defined ScamShield risk indicators
    patterns = {
        "payment_request": ["registration fee", "security deposit", "processing fee", "onboarding fee", "pay to join"],
        "urgency": ["apply immediately", "limited slots", "urgent hiring", "act fast", "today only"],
        "pii_request": ["aadhaar", "pan card", "bank account", "passport", "otp", "cvv"]
    }
    
    for f_type, keywords in patterns.items():
        for kw in keywords:
            if kw in text_lower:
                findings.append({
                    "type": f_type,
                    "severity": "critical" if f_type != "urgency" else "high",
                    "message": f"[Failsafe Mode] Detected {f_type.replace('_', ' ')} keywords: '{kw}'"
                })
                break

    return {
        "company_name": "Unknown",
        "job_title": "Unknown",
        "location": "Remote",
        "id": "local_fallback",
        "findings": findings
    }

# --- 3. Primary Analysis Engine ---
def analyze_text_with_ai(extracted_text: str) -> Dict[str, Any]:
    """
    Groq-Exclusive Analysis Architecture:
    Primary: Groq (Llama 3.1) -> Secondary: Local Keyword Engine.
    """
    
    SYSTEM_PROMPT = """You are an elite cyber-forensics investigator specializing in recruitment fraud.
Analyze the provided text and extract key entities. Then, identify specific 'red flags'.

REQUIRED OUTPUT FORMAT (JSON ONLY):
{
  "company_name": "Extract exact company name or 'Unknown'",
  "job_title": "Extract job title or 'Unknown'",
  "location": "Extract city/state/country or 'Remote'",
  "findings": [
    {
      "type": "payment_request|pii_request|urgency|unrealistic_salary",
      "severity": "low|medium|high|critical",
      "message": "Specific explanation of why this is a red flag"
    }
  ]
}"""

    # Safety: Token limit handling for large documents
    text_to_analyze = extracted_text[:15000]

    # --- STEP 1: GROQ PRIMARY ---
    if groq_client:
        try:
            print("🔄 Using Groq (Llama 3.1) as the exclusive AI engine...")
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text_to_analyze}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            result["id"] = "groq_primary"
            print(f"✅ Groq analysis complete: {len(result.get('findings', []))} findings")
            return result
        except Exception as e:
            print(f"⚠️ Groq Critical Error: {str(e)[:200]}")

    # --- STEP 2: LOCAL FAILSAFE ---
    print("🚨 Groq API failed or key missing. Using local keyword engine.")
    return _local_fallback_analysis(extracted_text)
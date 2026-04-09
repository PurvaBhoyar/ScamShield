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
    
    # Priority patterns based on defined JobShield risk indicators
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
    
    SYSTEM_PROMPT = """You are an elite cyber-forensics investigator specializing in recruitment fraud and scam detection.

Analyze the provided job offer text and extract key entities. Then, identify ALL red flags with detailed explanations.

REQUIRED OUTPUT FORMAT (JSON ONLY):
{
  "company_name": "Extract exact company name or 'Unknown'",
  "job_title": "Extract job title or 'Unknown'",
  "location": "Extract city/state/country or 'Remote'",
  "findings": [
    {
      "type": "payment_request|pii_request|urgency|unrealistic_salary|suspicious_job_claim|informal_contact|free_email_recruiter|template_match|blacklist_match|ai_generated_pattern|external_threat_match|typosquatting",
      "severity": "low|medium|high|critical",
      "message": "Specific explanation of why this is a red flag"
    }
  ],
  "confidence_score": 0-100,
  "analysis_summary": "Brief summary of why this is likely a scam or legitimate"
}

DETECTION CATEGORIES TO CHECK:
1. PAYMENT REQUESTS: Any mention of fees, deposits, payments (registration, processing, security, laptop, training, onboarding, membership, courier, verification, etc.) - CRITICAL
2. PII REQUESTS: Asking for Aadhaar, PAN, bank account, passport, OTP, CVV, ATM pin, date of birth, address - HIGH
3. URGENCY TACTICS: Words like "immediately", "limited time", "today only", "urgent", "last chance", "ASAP", "deadline" - MEDIUM
4. UNREALISTIC SALARY: Salary claims that seem too good to be true (>30k/month for entry-level, "earn 5000/day") - HIGH
5. SUSPICIOUS JOB CLAIMS: "No experience needed", "work from home", "part-time", "no interview", "fresher can apply" - MEDIUM
6. INFORMAL CONTACT: Requests to contact via WhatsApp, Telegram, personal phone instead of official email - HIGH
7. FREE EMAIL RECRUITER: Recruiter using @gmail.com, @yahoo.com, @hotmail.com instead of company domain - MEDIUM
8. SUSPICIOUS DOMAIN: Job posted on non-company domain, typosquatting (amazn.com, amaz0n.com) - CRITICAL
9. BLACKLIST PATTERNS: Known scam phrases or templates - CRITICAL
10. AI-GENERATED TEXT: Detect if text appears AI-generated with generic phrases - LOW

Be VERY thorough - look for ANY red flag. Better to report something than miss it."""

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
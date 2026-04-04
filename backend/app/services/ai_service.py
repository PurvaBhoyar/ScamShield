import os
import json
import re
from pathlib import Path
from google import genai
from groq import Groq
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# 1. Initialize Gemini Client
_google_raw = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_API_KEY = "".join(char for char in _google_raw if 32 <= ord(char) <= 126).strip()
gemini_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# 2. Initialize Groq Client (Fallback)
_groq_raw = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_KEY = "".join(char for char in _groq_raw if 32 <= ord(char) <= 126).strip()
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def _local_fallback_analysis(text: str) -> dict:
    """Hard-coded keyword analysis if all APIs fail."""
    findings = []
    text_lower = text.lower()
    
    # Red Flag Keywords
    patterns = {
        "payment_request": ["registration fee", "security deposit", "processing fee", "deposit", "pay to join"],
        "urgency": ["apply immediately", "limited slots", "urgent hiring", "act fast"],
        "pii_request": ["aadhaar", "pan card", "bank account", "passport", "otp", "cvv"]
    }
    
    for f_type, keywords in patterns.items():
        for kw in keywords:
            if kw in text_lower:
                findings.append({
                    "type": f_type,
                    "severity": "critical" if f_type != "urgency" else "high",
                    "message": f"Detected {f_type.replace('_', ' ')}: '{kw}'"
                })
                break

    return {
        "company_name": "Unknown",
        "job_title": "Unknown",
        "location": "Remote",
        "id": "local_fallback",
        "findings": findings
    }

def analyze_text_with_ai(extracted_text: str) -> dict:
    """Primary: Gemini 2.0 -> Secondary: Groq Llama 3.1 -> Tertiary: Local."""
    
    SYSTEM_PROMPT = """You are an elite cyber-forensics investigator specializing in recruitment fraud.
Analyze the provided job description/text and extract key entities. 
Then, identify specific 'red flags' based on these categories:
1. payment_request: Asking for money, deposits, or fees.
2. pii_request: Asking for sensitive data (PAN, Aadhaar, Bank, OTP).
3. urgency: Using high-pressure tactics or artificial deadlines.
4. unrealistic_salary: Compensation that is far above market rates.

Return ONLY a JSON object:
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

    # Clean input text
    text_to_analyze = extracted_text[:15000] # Token limit safety
    
    # --- STEP 1: TRY GEMINI (New SDK) ---
    if gemini_client:
        for model_id in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = gemini_client.models.generate_content(
                    model=model_id,
                    contents=[SYSTEM_PROMPT, text_to_analyze],
                    config={"response_mime_type": "application/json"}
                )
                if response and response.text:
                    raw_text = response.text
                    if "```json" in raw_text:
                        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_text:
                        raw_text = raw_text.split("```")[1].split("```")[0].strip()
                    
                    result = json.loads(raw_text)
                    result["id"] = f"gemini_{model_id}"
                    return result
            except Exception as e:
                print(f"⚠️ Gemini {model_id} Error: {str(e)[:100]}")
                continue

    # --- STEP 2: TRY GROQ FALLBACK ---
    if groq_client:
        try:
            print("🔄 Falling back to Groq (Llama 3.1)...")
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
            result["id"] = "groq_fallback"
            return result
        except Exception as e:
            print(f"⚠️ Groq Error: {str(e)[:100]}")

    # --- STEP 3: LOCAL FAILSAFE ---
    print("🚨 All AI APIs failed. Using local keyword engine.")
    return _local_fallback_analysis(extracted_text)

import os
import json
from dotenv import load_dotenv

# Initialize environment and client
load_dotenv()

# Use the new google genai library
try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"Gemini client init failed: {e}")
    client = None
    GEMINI_AVAILABLE = False

def analyze_text_with_ai(extracted_text: str) -> dict:
    """
    Analyzes extracted text using Gemini and returns a dictionary
    formatted to match the ScanResponse Pydantic schema.
    """
    if not GEMINI_AVAILABLE or not client:
        return _fallback_analysis(extracted_text)

    system_instruction = """
    You are an expert scam investigator. Analyze the text for specific red flags:
    1. Financial Requests: Any mention of deposit, fee, or payment for joining.
    2. Psychological Pressure: Urgency, limited slots, or "act now" tactics.
    3. Inconsistencies: Hinglish, poor grammar, or suspicious recruiter domains.
    4. PII Data: Requests for Aadhar, PAN, or Bank Details early.

    You MUST extract the 'company_name' and 'job_title' if available.
    If not found, set them to "Unknown".

    You MUST respond ONLY with a valid JSON object matching the exact schema below.
    Do not include markdown formatting.

    REQUIRED JSON SCHEMA:
    {
      "company_name": "<string: official company name extracted>",
      "job_title": "<string: job title extracted>",
      "id": "generated_by_ai",
      "score": <integer from 0 to 100>,
      "label": "<string: 'Safe', 'Caution', or 'Danger'>",
      "findings": [
        {
          "type": "payment_request|urgency|pii_request|grammar",
          "severity": "low|medium|high|critical",
          "message": "<string explanation>"
        }
      ],
      "evidence": ["<evidence snippet>"],
      "actions": ["<recommendation>"]
    }
    """

    # Try gemini-2.0-flash first
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash']

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[f"{system_instruction}\n\nTEXT TO ANALYZE:\n{extracted_text}"],
                config={
                    'response_mime_type': 'application/json',
                }
            )

            raw_text = response.text

            # Clean up potential markdown blocks
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            return json.loads(raw_text)

        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue

    # If all models fail, return fallback
    return _fallback_analysis(extracted_text)


def _fallback_analysis(extracted_text: str) -> dict:
    """Fallback analysis using simple keyword matching."""
    text_lower = extracted_text.lower()
    findings = []
    score = 0

    # Check for common scam keywords
    if any(word in text_lower for word in ['deposit', 'fee', 'payment', 'advance']):
        findings.append({
            "type": "payment_request",
            "severity": "high",
            "message": "Text mentions payment or deposit requirements"
        })
        score += 30

    if any(word in text_lower for word in ['urgent', 'limited time', 'act now', ' hurry']):
        findings.append({
            "type": "urgency",
            "severity": "medium",
            "message": "Text uses urgency tactics"
        })
        score += 20

    if any(word in text_lower for word in ['aadhar', 'pan card', 'bank details', 'otp']):
        findings.append({
            "type": "pii_request",
            "severity": "high",
            "message": "Text requests sensitive personal information"
        })
        score += 25

    label = 'Safe'
    if score >= 50:
        label = 'Danger'
    elif score >= 25:
        label = 'Caution'

    return {
        "company_name": "Unknown",
        "job_title": "Unknown",
        "id": "keyword_fallback",
        "score": min(score, 100),
        "label": label,
        "findings": findings,
        "evidence": [f"Analyzed {len(extracted_text)} characters of text"],
        "actions": ["Manual review recommended."],
    }
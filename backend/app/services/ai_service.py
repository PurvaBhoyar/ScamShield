import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Initialize environment and client
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analyze_text_with_ai(extracted_text: str) -> dict:
    """
    Analyzes extracted text using Gemini and returns a dictionary 
    formatted to match the ScanResponse Pydantic schema.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

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

    try:
        # Check if the model supports JSON response natively (v0.8.0+)
        # If not, fallback to plain text generation and manual JSON parsing
        try:
            response = model.generate_content(
                f"{system_instruction}\n\nTEXT TO ANALYZE:\n{extracted_text}",
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = response.text
        except (TypeError, ValueError):
            # Fallback for older SDK versions that don't support response_mime_type
            response = model.generate_content(
                f"{system_instruction}\n\nTEXT TO ANALYZE:\n{extracted_text}\n\nIMPORTANT: Return ONLY the JSON object, no markdown."
            )
            raw_text = response.text
            # Clean up potential markdown blocks
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        # Convert the JSON string response into a Python dictionary
        return json.loads(raw_text)

    except Exception as e:
        # Fallback mechanism in case of API failure
        print(f"AI Analysis Error: {e}")
        return {
            "id": "error_fallback",
            "score": 0,
            "label": "Safe",
            "findings": [],
            "evidence": ["AI processing failed."],
            "actions": ["Manual review recommended."],
            "policyLog": [{"action": "ai_analysis", "status": "failed", "reason": str(e)}]
        }

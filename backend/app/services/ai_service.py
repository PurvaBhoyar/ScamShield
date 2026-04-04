import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Initialize environment and client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_text_with_ai(extracted_text: str) -> dict:
    """
    Analyzes extracted text using Gemini and returns a dictionary 
    formatted to match the ScanResponse Pydantic schema.
    """
    model_id = 'gemini-2.5-flash'

    system_instruction = """
    You are an expert scam detection AI. Analyze the user's text and identify if it is a scam.
    You MUST respond ONLY with a valid JSON object matching the exact schema below. 
    Do not include markdown formatting.
    
    REQUIRED JSON SCHEMA:
    {
      "id": "generated_by_ai",
      "score": <integer from 0 to 100, where 100 is maximum danger>,
      "label": "<string: 'Safe', 'Caution', or 'Danger'>",
      "findings": [
        {
          "type": "<string>",
          "severity": "<string: 'low', 'medium', 'high', or 'critical'>",
          "message": "<string clearly explaining this specific red flag>"
        }
      ],
      "evidence": [
        "<string clearly detailing a piece of evidence found in the text>"
      ],
      "actions": [
        "<string recommending an exact action for the user to take>"
      ],
      "policyLog": [
        {
          "action": "ai_text_analysis",
          "status": "allowed",
          "reason": "Successfully processed text for soft signals"
        }
      ]
    }
    """

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=f"{system_instruction}\n\nTEXT TO ANALYZE:\n{extracted_text}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        # Convert the JSON string response into a Python dictionary
        return json.loads(response.text)

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
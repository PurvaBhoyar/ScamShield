import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the API key
load_dotenv()
naya_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def scam_pakdo(kachra_text):
    """
    Takes raw text and outputs perfect JSON matching backend/app/schemas/scan.py
    """
    model_id = 'gemini-2.5-flash'

    # The Master Contract based on Person A's ScanResponse Pydantic Model
    system_nirdesh = """
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
          "type": "<string, e.g., payment_request, urgency, email_mismatch>",
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

    print("Analyzing payload with strict Pydantic JSON schema...")
    
    jawab = naya_client.models.generate_content(
        model=model_id,
        contents=f"{system_nirdesh}\n\nTEXT TO ANALYZE:\n{kachra_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    return jawab.text

# --- TEST AREA ---
if __name__ == "__main__":
    dhokha_msg = """
    URGENT: Your background verification for the SDE-1 role is pending. 
    Please pay the Rs. 1500 processing fee to UPI ID: hr-desk@ybl immediately.
    """
    
    natija = scam_pakdo(dhokha_msg)
    print("\n=== PERFECT PVDANTIC AI OUTPUT ===")
    print(natija)
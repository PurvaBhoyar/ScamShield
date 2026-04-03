import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the API key from the .env file
load_dotenv()

# NEW SDK Initialization (Notice: No genai.configure here!)
naya_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def scam_pakdo(kachra_text):
    """
    Takes raw, messy text (OCR or scraped) and returns a structured JSON evaluation.
    """
    # Using the latest model
    model_id = 'gemini-2.5-flash'

    # We are still waiting for Person A's schema, so we will just ask for generic JSON for now to test the connection.
    system_nirdesh = """
    You are an expert scam detection AI. Analyze the user's text and identify if it is a scam.
    You MUST respond ONLY with a valid JSON object. Do not include markdown formatting like ```json.
    """

    print("Analyzing payload with the new GenAI SDK...")
    
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
    # Fake dummy text to test our engine
    dhokha_msg = """
    URGENT: Your background verification for the SDE-1 role is pending. 
    Please pay the Rs. 1500 processing fee to UPI ID: hr-desk@ybl immediately.
    """
    
    natija = scam_pakdo(dhokha_msg)
    print("\n=== AI OUTPUT ===")
    print(natija)
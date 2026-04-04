import os
from dotenv import load_dotenv
from google import genai
from PIL import Image

# Initialize environment and client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts raw text from an uploaded image file using Gemini's multimodal capabilities.
    """
    model_id = 'gemini-2.5-flash'
    
    try:
        # Load the image using Pillow (PIL)
        image_data = Image.open(image_path)
        
        # Strict instruction to only return the text, nothing else
        system_instruction = (
            "You are a highly accurate Optical Character Recognition (OCR) system. "
            "Extract all readable text from this image exactly as it appears. "
            "Do NOT add any conversational filler, explanations, or markdown. "
            "Return ONLY the raw extracted text."
        )
        
        print(f"Processing OCR for: {image_path}...")
        
        # Pass both the instruction and the image object to Gemini
        response = client.models.generate_content(
            model=model_id,
            contents=[system_instruction, image_data]
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"OCR Processing Error: {e}")
        return ""

# --- TEST AREA ---
if __name__ == "__main__":
    # To test this, you need a dummy image in your backend folder
    test_image_filename = "fak.jpeg"
    
    # Check if the file exists before running
    if os.path.exists(test_image_filename):
        extracted_text = extract_text_from_image(test_image_filename)
        print("\n=== EXTRACTED TEXT FROM IMAGE ===")
        print(extracted_text)
    else:
        print(f"\n[WAITING] Please save any sample image as 'fak.jpeg' inside the backend folder to test the OCR.")
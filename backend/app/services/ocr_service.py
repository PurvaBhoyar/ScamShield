import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import pytesseract

# Load .env from backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure Tesseract path (Windows typically installs here)
# Update this path if you installed Tesseract to a different location
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    print(f"✅ Tesseract configured: {TESSERACT_PATH}")
elif os.path.exists(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    print(f"✅ Tesseract configured: C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe")
else:
    print("⚠️ Tesseract not found at default paths. Set TESSERACT_PATH in .env")

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts raw text from an uploaded image file using Tesseract OCR.
    Pure local OCR - no external API required.
    """
    try:
        print(f"📷 Processing OCR for: {image_path}...")

        # Open the image
        image = Image.open(image_path)

        # Extract text using Tesseract
        text = pytesseract.image_to_string(
            image,
            lang='eng+hin',  # English and Hindi
            config='--psm 6'  # Assume uniform block of text
        )

        # Clean up the text
        cleaned_text = text.strip()

        if cleaned_text:
            print(f"✅ OCR Success ({len(cleaned_text)} chars)")
            return cleaned_text
        else:
            print("⚠️ No text detected in image")
            return ""

    except Exception as e:
        print(f"❌ OCR Processing Error: {e}")
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
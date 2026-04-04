import os
from PIL import Image, PdfImagePlugin
import pytesseract
from dotenv import load_dotenv

# Try to import Google Gemini for cloud OCR
try:
    from google import genai
    load_dotenv()
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"Gemini not available: {e}")
    GEMINI_AVAILABLE = False

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image using Gemini (primary) or pytesseract (fallback).
    For PDFs, uses pytesseract.
    """
    try:
        # Check if it's a PDF
        if image_path.lower().endswith('.pdf'):
            return _extract_from_pdf(image_path)

        # Try Gemini first (better quality)
        if GEMINI_AVAILABLE:
            try:
                from PIL import Image
                image_data = Image.open(image_path)
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[
                        "You are a highly accurate OCR system. Extract all readable text from this image exactly as it appears. Return ONLY the raw extracted text.",
                        image_data
                    ]
                )
                if response.text and response.text.strip():
                    return response.text.strip()
            except Exception as e:
                print(f"Gemini OCR failed: {e}")

        # Fallback to pytesseract (local, free)
        return _extract_with_tesseract(image_path)

    except Exception as e:
        print(f"OCR Processing Error: {e}")
        return ""


def _extract_with_tesseract(image_path: str) -> str:
    """Extract text using local pytesseract."""
    try:
        image = Image.open(image_path)
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"Tesseract OCR failed: {e}")
        return ""


def _extract_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pytesseract."""
    try:
        from pdf2image import convert_from_path
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        full_text = ""
        for image in images:
            text = pytesseract.image_to_string(image)
            full_text += text + "\n"
        return full_text.strip()
    except Exception as e:
        print(f"PDF extraction failed: {e}")
        # Try alternative: use pytesseract directly on first page
        try:
            # For PDF, we need pdf2image, if not available, return empty
            return ""
        except:
            return ""


# --- TEST AREA ---
if __name__ == "__main__":
    test_image = "test.png"
    if os.path.exists(test_image):
        text = extract_text_from_image(test_image)
        print("=== EXTRACTED TEXT ===")
        print(text)
    else:
        print("No test image found")
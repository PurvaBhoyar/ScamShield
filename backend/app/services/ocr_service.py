import os
import io
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import fitz  # PyMuPDF for PDF handling

# Load .env from backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure Tesseract path (Windows typically installs here)
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    print(f"✅ Tesseract configured: {TESSERACT_PATH}")
elif os.path.exists(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    print(f"✅ Tesseract configured: C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe")
else:
    print("⚠️ Tesseract not found. Set TESSERACT_PATH in .env or install Tesseract OCR")


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from image or PDF file.
    - Images: Uses Tesseract OCR with English + Hindi support
    - PDFs: Uses PyMuPDF to extract text, falls back to OCR if needed
    """
    try:
        print(f"📷 Processing file: {image_path}...")

        file_ext = os.path.splitext(image_path)[1].lower()

        # Handle PDF files
        if file_ext == '.pdf':
            return _extract_from_pdf(image_path)

        # Handle image files
        return _extract_from_image(image_path)

    except Exception as e:
        print(f"❌ OCR Processing Error: {e}")
        return ""


def _extract_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        text_parts = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # If page has text, use it
            if text.strip():
                text_parts.append(text)
            else:
                # Empty page - try OCR
                print(f"⚠️ Page {page_num + 1} is empty, trying OCR...")
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x for better OCR
                img_data = pix.tobytes("png")

                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(image, lang='eng+hin')
                if ocr_text.strip():
                    text_parts.append(ocr_text)

        doc.close()
        full_text = "\n".join(text_parts)

        if full_text.strip():
            print(f"✅ PDF OCR Success ({len(full_text)} chars from {len(text_parts)} pages)")
            return full_text.strip()
        else:
            print("⚠️ PDF is empty or unreadable")
            return ""

    except Exception as e:
        print(f"❌ PDF Error: {e}")
        return ""


def _extract_from_image(image_path: str) -> str:
    """Extract text from image using Tesseract."""
    try:
        # Open the image
        image = Image.open(image_path)

        # Convert to RGB if needed (handles RGBA, palette modes)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Extract text using Tesseract with multiple configs for better results
        configs = [
            '--psm 6',  # Assume uniform block of text
            '--psm 4',  # Assume a single column of text
            '--psm 3',  # Fully automatic page segmentation
        ]

        results = []
        for config in configs:
            text = pytesseract.image_to_string(
                image,
                lang='eng+hin',  # English and Hindi
                config=config
            )
            if text.strip():
                results.append(text.strip())

        # Use the longest result
        if results:
            full_text = max(results, key=len)
            print(f"✅ Image OCR Success ({len(full_text)} chars)")
            return full_text
        else:
            print("⚠️ No text detected in image")
            return ""

    except Exception as e:
        print(f"❌ Image OCR Error: {e}")
        return ""


# --- TEST AREA ---
if __name__ == "__main__":
    test_image = "test.jpg"
    test_pdf = "test.pdf"

    if os.path.exists(test_image):
        result = extract_text_from_image(test_image)
        print(f"\n=== IMAGE RESULT ({len(result)} chars) ===")
        print(result[:500])
    elif os.path.exists(test_pdf):
        result = extract_text_from_image(test_pdf)
        print(f"\n=== PDF RESULT ({len(result)} chars) ===")
        print(result[:500])
    else:
        print("No test files found. Add test.jpg or test.pdf to backend folder.")
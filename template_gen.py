from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
from PIL import Image
import pytesseract
import openai
import os

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# open image or convert pdf to image 

def image_from_file(file_path: str) -> Image.Image:
    """
    Opens an image or converts the first page of a PDF to an image.
    """
    ext = Path(file_path).suffix.lower()
    
    if ext == ".pdf":
        pages = convert_from_path(file_path, dpi=200, fmt="png")
        if not pages:
            raise ValueError("PDF conversion failed or file is empty.")
        return pages[0]
    else:
        return Image.open(file_path).convert("RGB")

# image preprocessing

def preprocess_image(img: Image.Image) -> Image.Image:
    # Convert to grayscale
    img = img.convert("L")
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    # Resize small images
    max_dim = 1200
    w, h = img.size
    if max(w, h) < max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
    return img

# Run ocr on image
def ocr_extract_text(file_path: str) -> str:
    """
    Runs Tesseract OCR on an image or PDF and returns extracted text.
    """
    img = image_from_file(file_path)
    img = preprocess_image(img)
    custom_config = r'--oem 3'
    text = pytesseract.image_to_string(img, config=custom_config)
    return text


# generate template
def generate_template(file_path: str) -> str:
    """
    Extracts transaction details from a receipt or bank document.

    Returns the text with dynamic fields replaced by placeholders.
    """
    ocr_text = ocr_extract_text(file_path)
    # print(ocr_text)

    prompt = f"""
You are an intelligent OCR assistant.

Input text:
{ocr_text}

Output the text with placeholders for dynamic values:

- {{sender_name}}
- {{sender_account}}
- {{sender_bank}}
- {{receiver_name}}
- {{receiver_account}}
- {{receiver_bank}}
- {{amount}}
- {{amount_in_words}}
- {{transaction_type}}
- {{date}}
- {{timestamp}}
- {{timezone}}
- {{transaction_reference}}
- {{session_id}}
- {{pos_transfer}}

Rules:
1. Replace only dynamic values, not labels.
2. Keep all static text, spacing, and line order exactly the same.
3. Output only the rewritten text with placeholders, nothing else.
"""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1000,
    )

    try:
        return response.choices[0].message.content
    except (KeyError, IndexError):
        return "Failed to generate template details."


# --- Example usage ---
if __name__ == "__main__":
    result = generate_template("test.pdf")

    print(result)

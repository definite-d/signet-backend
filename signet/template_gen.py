from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO
from typing import Literal
import openai

from .settings import settings

# OpenAI API key
openai.api_key = settings.OPENAI_API_KEY.get_secret_value()

# open image or convert pdf to image


def image_from_file(file_path) -> Image.Image:
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


def image_from_data(
    data: bytes, format: Literal["pdf", "webp", "jpg", "png"]
) -> Image.Image:
    stream = BytesIO(data)
    if format == "pdf":
        pages = convert_from_path(stream, dpi=200, fmt="png")
        if not pages:
            raise ValueError("PDF conversion failed or file is empty.")
        return pages[0]
    return Image.open(stream).convert("RGB")


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
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    return img


# Run ocr on image
def ocr_extract_text(file_path: str) -> str:
    """
    Runs Tesseract OCR on an image or PDF and returns extracted text.
    """
    img = image_from_file(file_path)
    img = preprocess_image(img)
    custom_config = r"--oem 3"
    text = pytesseract.image_to_string(img, config=custom_config)
    return text


# generate template
def generate_template(data: bytes) -> str:
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

Output the text with Jinja2 placeholders for dynamic values:

- {{{{ sender_name  }}}}
- {{{{ sender_bank  }}}}
- {{{{ receiver_name  }}}}
- {{{{ receiver_account  }}}}
- {{{{ receiver_bank  }}}}
- {{{{ amount  }}}}
- {{{{ amount_in_words  }}}}
- {{{{ transaction_type  }}}}
- {{{{ date  }}}}
- {{{{ timestamp  }}}}
- {{{{ timezone  }}}}
- {{{{ transaction_reference  }}}}
- {{{{ session_id  }}}}
- {{{{ pos_transfer  }}}}

Rules:
1. Replace only dynamic values, not labels.
2. Keep all static text, spacing, and line order exactly the same.
3. Output only the rewritten text with placeholders, nothing else.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1000,
        )
    except openai.APIError:
        raise EnvironmentError("OpenAI's API is currently unreachable")

    try:
        r = response.choices[0].message.content
        r = r.strip("```")
        return r
    except (KeyError, IndexError):
        raise ValueError("Failed to generate template details")


# --- Example usage ---
if __name__ == "__main__":
    from clipboard import copy

    copy(generate_template("test.pdf"))

import io
import base64
from pypdf import PdfReader

def process_pdf_content(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF file.
    """
    try:
        pdf = PdfReader(io.BytesIO(file_bytes))
        extracted_text = []

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)

        return "\n".join(extracted_text)
    except Exception as e:
        raise ValueError(f"Failed to process PDF: {str(e)}")

def process_image_content(file_bytes: bytes, content_type: str) -> str:
    """
    Converts image bytes to a base64 data URI string suitable for the OpenAI Vision API.
    """
    try:
        base64_img = base64.b64encode(file_bytes).decode('utf-8')
        return f"data:{content_type};base64,{base64_img}"
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")

from fastapi import APIRouter, UploadFile, HTTPException, File
from pydantic import BaseModel
from typing import List
from langchain_openai import ChatOpenAI
from app.routes.document_processor import process_pdf_content, process_image_content
from app.core.config import settings

router = APIRouter()

# Structured output for LangChain
class Flashcard(BaseModel):
    question: str
    answer: str

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]

@router.post("/generate", response_model=FlashcardResponse)
async def generate_flashcards(file: UploadFile = File(...)):
    api_key = settings.OPENAI_API_KEY
    if not api_key or api_key == "your_openai_api_key_here":
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")

    try:
        content_type = file.content_type
        file_bytes = await file.read()
        
        # Initialize OpenAI Chat model
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7).with_structured_output(FlashcardResponse)

        if content_type == "application/pdf":
            # Extract text from PDF
            extracted_text = process_pdf_content(file_bytes)
            
            if not extracted_text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

            prompt = f"Extract key concepts from the following text and generate flashcards. Text: {extracted_text}"
            response = llm.invoke(prompt)
            return response

        elif content_type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            # Process Image to Base64
            base64_image = process_image_content(file_bytes, content_type)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image, extract key concepts or text, and generate flashcards based on the content."},
                        {"type": "image_url", "image_url": {"url": base64_image}}
                    ]
                }
            ]
            response = llm.invoke(messages)
            return response

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

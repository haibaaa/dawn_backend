from fastapi import APIRouter, UploadFile, HTTPException, File
from langchain_openai import ChatOpenAI
from app.utils import process_pdf_content, process_image_content
from app.schemas import FlashcardResponse

router = APIRouter()


@router.post("/generate", response_model=list[dict])
async def generate_flashcards(file: UploadFile = File(...)):
    try:
        content_type = file.content_type
        file_bytes = await file.read()

        # Initialize OpenAI Chat model
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7).with_structured_output(
            FlashcardResponse
        )

        if content_type == "application/pdf":
            # Extract text from PDF
            extracted_text = process_pdf_content(file_bytes)

            if not extracted_text.strip():
                raise HTTPException(
                    status_code=400, detail="could not extract text from the pdf."
                )

            prompt = f"extract key concepts from the following text and generate flashcards. text: {extracted_text}"
            response = llm.invoke(prompt)

        elif content_type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            # Process Image to Base64
            base64_image = process_image_content(file_bytes, content_type)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "analyze this image, extract key concepts or text, and generate flashcards based on the content.",
                        },
                        {"type": "image_url", "image_url": {"url": base64_image}},
                    ],
                }
            ]
            response = llm.invoke(messages)

        else:
            raise HTTPException(
                status_code=400, detail=f"unsupported file type: {content_type}"
            )

        flashcard_items = []
        if response and hasattr(response, "flashcards"):
            for f in response.flashcards:
                f_dict = f.model_dump()
                f_dict["type"] = "flashcard"
                flashcard_items.append(f_dict)

        return flashcard_items

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

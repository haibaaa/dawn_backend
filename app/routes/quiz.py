from fastapi import APIRouter, UploadFile, HTTPException, File, Depends
from langchain_openai import ChatOpenAI
from app.utils import process_pdf_content, process_image_content, get_current_user
from app.schemas import QuizResponse

router = APIRouter()


@router.post("/generate", response_model=list[dict])
async def generate_quiz(
    file: UploadFile = File(...),
):
    try:
        content_type = file.content_type
        file_bytes = await file.read()

        llm = ChatOpenAI(model="gpt-4o", temperature=0.5).with_structured_output(
            QuizResponse
        )

        quiz_prompt_text = """
        analyze the following material and generate a challenging multiple-choice quiz.
        create 10 high-quality questions that test conceptual understanding, not just definitions.
        
        for each question:
        1. set 'type' to 'quiz'.
        2. provide 4 plausible options (1 correct, 3 distractors).
        3. include a concise 'explanation' of why the correct answer is right.
        """

        if content_type == "application/pdf":
            extracted_text = process_pdf_content(file_bytes)
            if not extracted_text.strip():
                raise HTTPException(
                    status_code=400, detail="Could not extract text from the file."
                )

            prompt = f"{quiz_prompt_text}\n\nText content: {extracted_text[:15000]}"
            ai_response = llm.invoke(prompt)

        elif content_type in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            base64_image = process_image_content(file_bytes, content_type)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": quiz_prompt_text,
                        },
                        {"type": "image_url", "image_url": {"url": base64_image}},
                    ],
                }
            ]
            ai_response = llm.invoke(messages)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {content_type}"
            )

        quiz_items = []
        if ai_response and hasattr(ai_response, "questions"):
            for q in ai_response.questions:
                q_dict = q.model_dump()
                q_dict["type"] = "quiz"
                quiz_items.append(q_dict)

        return quiz_items

    except Exception as e:
        print(f"Error details: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

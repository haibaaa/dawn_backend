from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Resource
from app.core.supabase_client import supabase
from app.utils import get_and_sync_user
from app.core.config import settings
import uuid

router = APIRouter()


@router.post("/upload")
async def upload_resource(
    title: str = Form(...),
    tags: str = Form(...),
    course_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_and_sync_user),
):
    try:
        # generate unique file path
        file_ext = file.filename.split(".")[-1] if file.filename else "pdf"
        file_path = f"{uuid.uuid4()}.{file_ext}"

        # upload to supabase storage
        file_content = await file.read()

        # keep path=file_path for the storage call itself
        supabase.storage.from_("resources").upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type},
        )

        # construct the full public url
        # strip any trailing slashes to prevent "double slash" bugs
        base_url = settings.SUPABASE_BUCKET_URL.rstrip("/")
        full_public_url = f"{base_url}/{file_path}"

        # save metadata to database
        tag_list = [t.strip() for t in tags.split(",")]

        new_resource = Resource(
            title=title,
            file_url=full_public_url,  # Store the permanent link
            tags=tag_list,
            user_id=current_user.id,  # Use the actual synced user ID
            course_id=course_id,
        )

        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        return {"message": "resource uploaded successfully", "resource": new_resource}

    except Exception as e:
        # In a real app, you'd add: supabase.storage.from_("resources").remove([file_path])
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

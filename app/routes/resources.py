from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Resource
from app.core.supabase_client import supabase
from app.utils import get_and_sync_user, get_current_user
from app.core.config import settings
import uuid

router = APIRouter(
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
async def search_resources(
    tags: list[str] = Query(None),
    course_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_and_sync_user),
):
    """
    Public Resource Bank: Fetch resources from all users.
    If tags are provided, returns resources that have ANY of those tags (Overlap).
    """
    try:
        # Start with all resources in the bank
        query = db.query(Resource)

        # Optional: Filter by course
        if course_id:
            query = query.filter(Resource.course_id == course_id)

        # Overlap Search Logic
        if tags:
            # Matches any resource where the tags array has elements in common with the search list
            query = query.filter(Resource.tags.overlap(tags))

        return query.all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


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
        # 1. Generate unique file path
        file_ext = file.filename.split(".")[-1] if file.filename else "pdf"
        file_path = f"{uuid.uuid4()}.{file_ext}"

        # 2. Upload to supabase storage
        file_content = await file.read()
        supabase.storage.from_("resources").upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type},
        )

        # 3. Construct public URL
        base_url = settings.SUPABASE_BUCKET_URL.rstrip("/")
        full_public_url = f"{base_url}/{file_path}"

        # 4. Save metadata
        # Splitting the comma-separated string from the Form into a clean list
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        new_resource = Resource(
            title=title,
            file_url=full_public_url,
            tags=tag_list,
            user_id=current_user.id,  # Record who contributed the resource
            course_id=course_id,
        )

        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        return {"message": "resource uploaded successfully", "resource": new_resource}

    except Exception as e:
        # Note: In production, consider deleting the file from Supabase storage here if DB save fails
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

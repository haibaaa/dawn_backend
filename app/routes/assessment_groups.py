from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from app.core.database import get_db
from app.utils import (
    check_enrolled,
    get_current_user,
    get_and_sync_user,
    get_course_or_404,
)

router = APIRouter(
    dependencies=[Depends(get_current_user)],
)


def validate_group_fields(
    weight: float | None,
    count: int | None,
    best_of: int | None,
    existing_count: int | None = None,
):
    if weight is not None and not 0 < weight <= 1:
        raise HTTPException(status_code=400, detail="weight must be between 0 and 1")
    if count is not None and count <= 0:
        raise HTTPException(status_code=400, detail="count must be positive")
    effective_count = count if count is not None else existing_count
    if (
        best_of is not None
        and effective_count is not None
        and best_of > effective_count
    ):
        raise HTTPException(status_code=400, detail="best_of cannot exceed count")


@router.post(
    "/",
    response_model=schemas.AssessmentGroupOut,
    status_code=201,
    response_model_exclude_none=True,
)
def create_assessment_group(
    assessment_group: schemas.AssessmentGroupCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    course = get_course_or_404(db, assessment_group.course_code)
    check_enrolled(db, user.id, course.id)
    validate_group_fields(
        assessment_group.weight, assessment_group.count, assessment_group.best_of
    )

    new_group = models.AssessmentGroup(
        name=assessment_group.name,
        weight=assessment_group.weight,
        count=assessment_group.count,
        best_of=assessment_group.best_of,
        course_id=course.id,
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.patch(
    "/{id}", response_model=schemas.AssessmentGroupOut, response_model_exclude_none=True
)
def update_assessment_group(
    id: int,
    updated_group: schemas.AssessmentGroupUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    group = (
        db.query(models.AssessmentGroup).filter(models.AssessmentGroup.id == id).first()
    )
    if not group:
        raise HTTPException(status_code=404, detail=f"Assessment group {id} not found")

    check_enrolled(db, user.id, group.course_id)
    updated_data = updated_group.dict(exclude_unset=True)
    validate_group_fields(
        updated_data.get("weight"),
        updated_data.get("count"),
        updated_data.get("best_of"),
        existing_count=group.count,
    )

    for field, value in updated_data.items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)
    return group


@router.delete("/{id}", status_code=204)
def delete_assessment_group(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    group = (
        db.query(models.AssessmentGroup).filter(models.AssessmentGroup.id == id).first()
    )
    if not group:
        raise HTTPException(status_code=404, detail=f"Assessment group {id} not found")

    check_enrolled(db, user.id, group.course_id)
    db.delete(group)
    db.commit()


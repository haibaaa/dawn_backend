
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import models
from app.schemas import schemas
from app.core.database import get_db
from app.utils import check_enrolled, get_and_sync_user

router = APIRouter(prefix="/assessments", tags=['Assessments'])

# routers/assessments.py

# POST /assessments — add assessment to a group
# PATCH /assessments/{id} — update assessment details (max_score, deadline)
# DELETE /assessments/{id} — remove an assessment


def get_assessment_or_404(db: Session, id: int) -> models.Assessment:
    assessment = db.query(models.Assessment).filter(models.Assessment.id == id).first()

    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {id} not found")
    return assessment

def validate_assessment_fields(max_score: float | None, deadline: datetime | None):
    if max_score is not None and max_score <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_score must be positive")
    if deadline is not None and deadline < datetime.now(deadline.tzinfo):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="deadline cannot be in the past")

@router.post('/', response_model=schemas.AssessmentOut, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_assessment(assessment: schemas.AssessmentCreate, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):

    group = db.query(models.AssessmentGroup).filter(models.AssessmentGroup.id == assessment.assessment_group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail=f"Assessment group {assessment.assessment_group_id} not found")

    check_enrolled(db, user.id, group.course_id)
    validate_assessment_fields(assessment.max_score, assessment.deadline)

    new_assessment = models.Assessment(
        name=assessment.name,
        max_score=assessment.max_score,
        deadline=assessment.deadline,
        assessment_group_id=assessment.assessment_group_id
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return new_assessment

@router.patch('/{id}', response_model=schemas.AssessmentOut, response_model_exclude_none=True)
def update_assessment(id: int, updated_assessment: schemas.AssessmentUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):
    assessment = get_assessment_or_404(db, id)

    check_enrolled(db, user.id, assessment.assessment_group.course_id)

    updated_data = updated_assessment.dict(exclude_unset=True)
    validate_assessment_fields(
        updated_data.get("max_score"),
        updated_data.get("deadline")
    )

    for field, value in updated_data.items():
        setattr(assessment, field, value)

    db.commit()
    db.refresh(assessment)
    return assessment

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(id: int, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):
    assessment = get_assessment_or_404(db, id)
    check_enrolled(db, user.id, assessment.assessment_group.course_id)
    db.delete(assessment)
    db.commit()
    
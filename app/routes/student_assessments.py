
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from app.models import models
from app.schemas import schemas
from app.core.database import get_db
from app.utils import check_enrolled, calculate_current_score, get_and_sync_user
from app.utils.prioritiser import PriorityEngine

router = APIRouter(prefix="/student-assessments", tags=['Student Assessments'])

# routers/student_assessments.py

# POST /student-assessments — record a score for an assessment, triggers current_score recalculation on enrollment
# PATCH /student-assessments/{assessment_id} — update a recorded score, triggers recalculation
# GET /student-assessments — get all recorded scores for current user

def get_student_assessment_or_404(db: Session, user_id: str, assessment_id: int) -> models.StudentAssessment:
    sa = db.query(models.StudentAssessment).filter(
        models.StudentAssessment.user_id == user_id,
        models.StudentAssessment.assessment_id == assessment_id
    ).first()
    if not sa:
        raise HTTPException(status_code=404, detail=f"Score for assessment {assessment_id} not found")
    return sa

def get_course_id_for_assessment(db: Session, assessment_id: int) -> int:
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")
    return assessment.assessment_group.course_id

def update_enrollment_score(db: Session, user_id: str, course_id: int):
    PriorityEngine.update_all_priorities(db, user.id)
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == user_id,
        models.Enrollment.course_id == course_id
    ).first()
    if enrollment:
        score, weight_attempted = calculate_current_score(db, user_id, course_id)
        enrollment.current_score = score
        if weight_attempted >= 1.0:
            enrollment.final_score = score

@router.get('/', response_model=List[schemas.StudentAssessmentOut], response_model_exclude_none=True)
def get_student_assessments(course_code: str | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):

    query = (
        db.query(models.StudentAssessment)
        .join(models.Assessment)
        .join(models.AssessmentGroup)
        .join(models.Course)
        .filter(models.StudentAssessment.user_id == user.id)
    )

    if course_code:
        query = query.filter(models.Course.course_code == course_code.upper())

    return query.all()

@router.post('/', response_model=schemas.StudentAssessmentOut, status_code=201, response_model_exclude_none=True)
def record_score(student_assessment: schemas.StudentAssessmentCreate, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):

    # check not already recorded
    existing = db.query(models.StudentAssessment).filter(
        models.StudentAssessment.user_id == user.id,
        models.StudentAssessment.assessment_id == student_assessment.assessment_id
    ).first()

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score already recorded for this assessment — use PATCH to update")

    # validate score
    
    # single query
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == student_assessment.assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # use it for course_id
    course_id = assessment.assessment_group.course_id
    check_enrolled(db, user.id, course_id)

    if assessment.max_score and student_assessment.score > assessment.max_score:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Score cannot exceed max score of {assessment.max_score}")
    if student_assessment.score < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score cannot be negative")

    new_sa = models.StudentAssessment(
        user_id=user.id,
        assessment_id=student_assessment.assessment_id,
        score=student_assessment.score
    )
    db.add(new_sa)
    db.flush()  # ← flush first so calculate_current_score sees the new score
    update_enrollment_score(db, user.id, course_id)
    db.commit()
    db.refresh(new_sa)
    return new_sa

@router.patch('/{assessment_id}', response_model=schemas.StudentAssessmentOut, response_model_exclude_none=True)
def update_score(assessment_id: int, updated: schemas.StudentAssessmentUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):

    sa = get_student_assessment_or_404(db, user.id, assessment_id)
    course_id = get_course_id_for_assessment(db, assessment_id)
    check_enrolled(db, user.id, course_id)

    # validate new score
    if updated.score is not None:
        assessment = db.query(models.Assessment).filter(
            models.Assessment.id == assessment_id
        ).first()
        if assessment.max_score and updated.score > assessment.max_score:
            raise HTTPException(status_code=400, detail=f"Score cannot exceed max score of {assessment.max_score}")
        if updated.score < 0:
            raise HTTPException(status_code=400, detail="Score cannot be negative")
        sa.score = updated.score

    update_enrollment_score(db, user.id, course_id)

    db.commit()
    db.refresh(sa)
    return sa

@router.delete('/{assessment_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_score(assessment_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):

    sa = get_student_assessment_or_404(db, user.id, assessment_id)
    course_id = get_course_id_for_assessment(db, assessment_id)
    check_enrolled(db, user.id, course_id)

    db.delete(sa)

    # recalculate score after deletion
    update_enrollment_score(db, user.id, course_id)

    db.commit()
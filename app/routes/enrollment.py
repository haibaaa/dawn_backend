from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from app.schemas import schemas
from app.models import models
from app.core.database import get_db
from app.utils import get_valid_courses, get_enrollment_or_404
from app.utils.get_and_sync_user import get_and_sync_user


router = APIRouter(
    prefix="/enrollments",
    tags=['Enrollments']
)

# POST /enrollments — validate course against Excel, create course in DB if first enrollment, enroll user, return EnrollmentOut
# GET /enrollments — get all courses user is enrolled in with current scores and progress
# GET /enrollments/{course_id} — detailed view of single course with assessment groups, assessments, scores, projected score, what's needed to hit target
# PATCH /enrollments/{course_id} — update target score/grade

# Helper Function
def validate_target_score(target_score: float | None):
    if target_score is not None and not 0 <= target_score <= 100:
        raise HTTPException(status_code=400, detail="target_score must be between 0 and 100")
    
# Routes

@router.get('/', response_model=List[schemas.EnrollmentOut], response_model_exclude_none=True)
def get_enrollments(db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):
    return db.query(models.Enrollment).filter(models.Enrollment.user_id == user.id).all()

@router.get('/{id}', response_model=schemas.EnrollmentOut, response_model_exclude_none=True)
def get_enrollment(id: int, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):
    return get_enrollment_or_404(db, user.id, id)
 
@router.post('/', response_model=schemas.EnrollmentOut, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_enrollment(enrollment: schemas.EnrollmentCreate, db: Session = Depends(get_db), valid_courses: dict = Depends(get_valid_courses), user: models.User = Depends(get_and_sync_user)):
    enrollment_data = enrollment.dict()
    course_code = enrollment_data.get("course_code").upper()

    validate_target_score(enrollment_data.get("target_score"))

    if course_code not in valid_courses:
        raise HTTPException(status_code=400, detail="Course not offered this semester")

    course = db.query(models.Course).filter(models.Course.course_code == course_code).first()
    if not course:
        course = models.Course(course_code=course_code, name=valid_courses[course_code])
        db.add(course)
        db.flush()

    existing = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == user.id,
        models.Enrollment.course_id == course.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    new_enrollment = models.Enrollment(
        user_id=user.id,
        course_id=course.id,
        target_score=enrollment_data.get("target_score"),
        target_grade=enrollment_data.get("target_grade")
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

@router.patch('/{id}', response_model=schemas.EnrollmentOut, response_model_exclude_none=True)
def update_target(id: int, targets: schemas.EnrollmentUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):
    enrollment = get_enrollment_or_404(db, user.id, id)
    target_data = targets.dict(exclude_unset=True)

    validate_target_score(target_data.get("target_score"))

    for field, value in target_data.items():
        setattr(enrollment, field, value)

    db.commit()
    db.refresh(enrollment)
    return enrollment

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(id: int, db: Session = Depends(get_db), user: models.User = Depends(get_and_sync_user)):
    enrollment = get_enrollment_or_404(db, user.id, id)
    db.delete(enrollment)
    db.commit()
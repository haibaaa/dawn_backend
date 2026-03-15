from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from app.models import models
from app.core.database import get_db
from app.utils import get_valid_courses

router = APIRouter(
    prefix="/courses",
    tags=['Courses']
)
# GET /courses/{course_id} — get course details with nested assessment groups and assessments (for viewing structure)
# GET /courses — search available courses (reads from Excel, not DB) so user can see what's offered before enrolling

@router.get('/', response_model_exclude_none=True)
def get_offered_courses(valid_courses: dict = Depends(get_valid_courses)):
    return [{"course_code": code, "name": name} for code, name in valid_courses.items()]

@router.get('/code/{course_code}', response_model_exclude_none=True)
def get_course_by_code(course_code: str, db: Session = Depends(get_db), valid_courses: dict = Depends(get_valid_courses)):
    code = course_code.upper()

    course = (
        db.query(models.Course)
        .options(
            joinedload(models.Course.assessment_groups)
            .joinedload(models.AssessmentGroup.assessments)
        )
        .filter(models.Course.course_code == code)
        .first()
    )

    if course:
        return course

    if code in valid_courses:
        return {
            "course_code": code,
            "name": valid_courses[code],
            "message": "This course is offered this semester but no assessment details are available yet"
        }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {code} is not offered this semester")
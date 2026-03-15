from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import models

valid_courses = {}

def get_valid_courses():
    return valid_courses

def get_course_or_404(db: Session, course_code: str) -> models.Course:
    course = db.query(models.Course).filter(
        models.Course.course_code == course_code.upper()
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course {course_code} not found")
    return course

def check_enrolled(db: Session, user_id: str, course_id: int) -> models.Enrollment:
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == user_id,
        models.Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    return enrollment

def get_enrollment_or_404(db: Session, user_id: str, course_id: int) -> models.Enrollment:
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == user_id,
        models.Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail=f"Enrollment for course {course_id} not found")
    return enrollment

def calculate_current_score(db: Session, user_id: str, course_id: int) -> tuple[float, float]:
    groups = db.query(models.AssessmentGroup).filter(
        models.AssessmentGroup.course_id == course_id
    ).all()

    total_score = 0.0
    total_weight_attempted = 0.0

    for group in groups:
        # get all recorded scores for this group
        student_scores = (
            db.query(models.StudentAssessment, models.Assessment)
            .join(models.Assessment)
            .filter(
                models.Assessment.assessment_group_id == group.id,
                models.StudentAssessment.user_id == user_id,
                models.StudentAssessment.score.isnot(None)
            )
            .all()
        )

        if not student_scores:
            continue

        # build (score, max_score) pairs
        pairs = [
            (sa.score, a.max_score)
            for sa, a in student_scores
            if a.max_score and a.max_score > 0
        ]

        if not pairs:
            continue

        # apply best_of policy
        if group.best_of:
            # sort by percentage descending, take top best_of
            pairs = sorted(pairs, key=lambda x: x[0] / x[1], reverse=True)
            # pad with zeros if fewer attempts than best_of
            while len(pairs) < group.best_of:
                pairs.append((0, pairs[0][1]))  # use same max_score as others
            pairs = pairs[:group.best_of]
        
        # calculate group percentage
        total_earned = sum(p[0] for p in pairs)
        total_possible = sum(p[1] for p in pairs)

        if total_possible > 0:
            group_percentage = (total_earned / total_possible) * 100
            total_score += group_percentage * group.weight
            total_weight_attempted += group.weight

    if total_weight_attempted == 0:
        return 0.0, 0.0  # ← return tuple here too
    
    # scale to attempted weight only
    return round(total_score / total_weight_attempted, 2), round(total_weight_attempted, 2)

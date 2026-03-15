from fastapi import Query, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from datetime import date
from app.models import models
from app.schemas import schemas
from app.core.database import get_db
from app.utils import get_priority, get_and_sync_user, get_current_user

router = APIRouter(
    dependencies=[Depends(get_current_user)],
)


def validate_task_relations(
    db: Session, course_id: int | None, assessment_id: int | None
):
    """validates that course and assessment exist and are linked correctly."""
    if course_id:
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="course not found")

    if assessment_id:
        assessment = (
            db.query(models.Assessment)
            .filter(models.Assessment.id == assessment_id)
            .first()
        )
        if not assessment:
            raise HTTPException(status_code=404, detail="assessment not found")

        # Cross-validation
        if not course_id:
            raise HTTPException(
                status_code=400, detail="course_id required for assessment"
            )
        if assessment.assessment_group.course_id != course_id:
            raise HTTPException(status_code=400, detail="assessment/course mismatch")


def handle_dependencies(
    db: Session, task_id: int, dep_ids: list[int] | None, is_dependent: bool = False
):
    """Generic handler for task relationships."""
    if not dep_ids:
        return

    if task_id in dep_ids:
        raise HTTPException(status_code=400, detail="task cannot depend on itself")

    # Verify existence
    found = db.query(models.Task.id).filter(models.Task.id.in_(dep_ids)).all()
    if len(found) != len(dep_ids):
        raise HTTPException(
            status_code=404, detail="one or more related tasks not found"
        )

    for d_id in dep_ids:
        new_rel = models.TaskDependency(
            task_id=task_id if not is_dependent else d_id,
            depends_on_task_id=d_id if not is_dependent else task_id,
        )
        db.add(new_rel)


# --- Routes ---


@router.get("/", response_model=list[schemas.TaskResponse])
def get_tasks(
    task_status: schemas.Status = schemas.Status.PENDING,
    sort_by: str = "priority",
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    query = db.query(models.Task).filter(models.Task.user_id == user.id)
    query = query.filter(models.Task.status == task_status)

    # Simple sort mapping
    col = getattr(models.Task, sort_by, models.Task.priority)
    return query.order_by(col.desc()).limit(limit).all()


@router.post("/", response_model=schemas.TaskResponse, status_code=201)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    # 1. Convert Pydantic model to dictionary
    data = task_in.dict()

    # 2. Extract relationships that don't belong in the main Task table
    dep_ids = data.pop("dependencies", [])
    det_ids = data.pop("dependents", [])

    # 3. Business Validations
    validate_task_relations(db, data.get("course_id"), data.get("assessment_id"))
    if data.get("deadline") and data["deadline"] < date.today():
        raise HTTPException(status_code=400, detail="deadline cannot be in the past")

    # 4. Calculate Priority and update the dictionary
    # By putting it in 'data', we ensure it gets unpacked into the model correctly
    data["priority"] = get_priority(
        deadline=data.get("deadline"),
        estimated_hours=data.get("estimated_hours", 0),
        grade_impact=data.get("grade_impact", 0),
    )

    # 5. Construct the Task model
    # We unpack **data (which now includes the new priority) and add the user_id
    new_task = models.Task(**data, user_id=user.id)

    # 6. Database Transaction
    try:
        db.add(new_task)
        db.flush()  # Pushes to DB temporarily to generate new_task.id

        # Handle the many-to-many relationship links
        handle_dependencies(db, new_task.id, dep_ids)
        handle_dependencies(db, new_task.id, det_ids, is_dependent=True)

        db.commit()
        db.refresh(new_task)
        return new_task

    except Exception as e:
        db.rollback()
        # Log the error here if you have a logger
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{id}", status_code=204)
def delete_task(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == id, models.Task.user_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(404, "Task not found")

    db.delete(task)
    db.commit()


@router.patch("/{id}", response_model=schemas.TaskResponse)
def update_task(
    id: int,
    task_update: schemas.TaskUpdate,  # Note: Uses a different schema for partial updates
    db: Session = Depends(get_db),
    user: models.User = Depends(get_and_sync_user),
):
    # 1. Fetch the existing task
    task = (
        db.query(models.Task)
        .filter(models.Task.id == id, models.Task.user_id == user.id)
        .first()
    )

    if not task:
        raise HTTPException(404, "Task not found")

    # 2. Extract data to update
    update_data = task_update.dict(exclude_unset=True)  # Only update what's in the JSON

    # 3. Recalculate priority if relevant fields changed
    # We combine existing task data with the new updates
    new_deadline = update_data.get("deadline", task.deadline)
    new_hours = update_data.get("estimated_hours", task.estimated_hours)
    new_impact = update_data.get("grade_impact", task.grade_impact)

    update_data["priority"] = get_priority(
        deadline=new_deadline, estimated_hours=new_hours, grade_impact=new_impact
    )

    # 4. Apply updates to the model
    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=str(e))

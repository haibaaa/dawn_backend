from fastapi import Query, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy import nulls_last
from sqlalchemy.orm import Session
from typing import List
# from .. import oauth2
from models import models
from schemas import schemas
from core.database import get_db
from ..utils import get_priority
from ..enums import Status
from datetime import date

router = APIRouter(
    prefix="/tasks",
    tags=['Tasks']
)


@router.get('/', response_model=List[schemas.TaskResponse], response_model_exclude_none=True)
def get_tasks(task_status: Status | None = None, sort_by: str = "priority", order: str | None = None, limit: int = Query(10, le=100), skip: int = 0, db: Session = Depends(get_db)):
    query = db.query(models.Task)
    # query = query.filter(models.Task.user_id == current_user.id)

    if task_status:
        query = query.filter(models.Task.status == task_status)
    else:
        query = query.filter(models.Task.status == Status.pending)

    sort_columns = {
        "priority": models.Task.priority,
        "deadline": models.Task.deadline,
        "created_at": models.Task.created_at,
        "estimated_hours": models.Task.estimated_hours,
    }

    if sort_by not in sort_columns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"sort_by must be one of {list(sort_columns.keys())}")

    col = sort_columns[sort_by]

    if order == "asc":
        query = query.order_by(nulls_last(col.asc()))
    elif order == "desc" or order is None:
        query = query.order_by(nulls_last(col.desc()))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="order must be 'asc' or 'desc'")
    
    tasks = query.limit(limit).offset(skip).all()
    return tasks

@router.get('/{id}', response_model= schemas.TaskResponse, response_model_exclude_none=True)
def get_task(id: int, db: Session = Depends(get_db)):
    # query = query.filter(models.Task.user_id == current_user.id)
    task = db.query(models.Task).filter(models.Task.id == id).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"task with id: {id} was not found")
    
    return task


@router.post('/', response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    task_data = task.dict()
    task_data["user_id"] = 1  # ← hardcode for testing, remove when auth is wired in

    dependency_ids = task_data.pop("dependencies", None)
    dependent_ids = task_data.pop("dependents", None)

    if task_data.get("course_id") is not None:
        if not db.query(models.Course).filter(models.Course.id == task_data["course_id"]).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if task_data.get("assessment_id") is not None:
        assessment = (db.query(models.Assessment).join(models.AssessmentGroup).filter(models.Assessment.id == task_data["assessment_id"]).first())

        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

        # get the course_id to check against — either from the update or the existing task
        course_id_to_check = task_data.get("course_id")
        if not course_id_to_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course_id is required when setting assessment_id")

        if assessment.assessment_group.course_id != course_id_to_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment does not belong to the specified course")

    if task_data.get("estimated_hours") is not None and task_data["estimated_hours"] < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="estimated_hours must be positive")
    
    if task_data.get("deadline") is not None and task_data["deadline"] < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="deadline cannot be in the past")

    priority = get_priority(**task_data)
    new_task = models.Task(priority=priority, **task_data)
    db.add(new_task)

    try:
        db.flush() 
        if dependency_ids and new_task.id in dependency_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot depend on itself")

        if dependent_ids and new_task.id in dependent_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot depend on itself")

        if dependency_ids and dependent_ids:
            overlap = set(dependency_ids) & set(dependent_ids)
            if overlap:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task IDs {overlap} cannot be both dependencies and dependents")

        if dependency_ids:
            found = db.query(models.Task.id).filter(models.Task.id.in_(dependency_ids)).all()
            found_ids = {row.id for row in found}
            missing = set(dependency_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tasks with ids {missing} not found")

        if dependent_ids:
            found = db.query(models.Task.id).filter(models.Task.id.in_(dependent_ids)).all()
            found_ids = {row.id for row in found}
            missing = set(dependent_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tasks with ids {missing} not found")

        if dependency_ids:
            for dep_id in dependency_ids:
                db.add(models.TaskDependency(task_id=new_task.id, depends_on_task_id=dep_id))

        if dependent_ids:
            for dep_id in dependent_ids:
                db.add(models.TaskDependency(task_id=dep_id, depends_on_task_id=new_task.id))

        db.commit()
        db.refresh(new_task)
        return new_task

    except Exception:
        db.rollback()
        raise

@router.put('/{id}', response_model= schemas.TaskResponse)
def update_task_full(id: int, updated_task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    query = db.query(models.Task).filter(models.Task.id == id)
    task = query.first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"task with id: {id} was not found")
    
    updated_task_data = updated_task.dict()
    updated_task_data["user_id"] = 1  # ← hardcode for testing, remove when auth is wired in

    dependency_ids = updated_task_data.pop("dependencies", None)
    dependent_ids = updated_task_data.pop("dependents", None)

    if updated_task_data.get("course_id") is not None:
        if not db.query(models.Course).filter(models.Course.id == updated_task_data["course_id"]).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if updated_task_data.get("assessment_id") is not None:
        assessment = (db.query(models.Assessment).join(models.AssessmentGroup).filter(models.Assessment.id == updated_task_data["assessment_id"]).first())
        
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        
        # get the course_id to check against — either from the update or the existing task
        course_id_to_check = updated_task_data.get("course_id", task.course_id)

        if not course_id_to_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course_id is required when setting assessment_id")
        
        if assessment.assessment_group.course_id != course_id_to_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment does not belong to the specified course")

    if updated_task_data.get("estimated_hours") is not None and updated_task_data["estimated_hours"] < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="estimated_hours must be positive")
    
    if updated_task_data.get("deadline") is not None and updated_task_data["deadline"] < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="deadline cannot be in the past")

    priority_data = {
            "deadline": updated_task_data.get("deadline", task.deadline),
            "estimated_hours": updated_task_data.get("estimated_hours", task.estimated_hours),
            "grade_impact": updated_task_data.get("grade_impact", task.grade_impact),
            "course_id": updated_task_data.get("course_id", task.course_id),
            "assessment_id": updated_task_data.get("assessment_id", task.assessment_id),
    }

    priority = get_priority(**priority_data)
    updated_task_data["priority"] = priority

    try:
        query.update(updated_task_data, synchronize_session=False)
        db.query(models.TaskDependency).filter(models.TaskDependency.task_id == id).delete()
        db.query(models.TaskDependency).filter(models.TaskDependency.depends_on_task_id == id).delete()
        db.flush() 
        
        if dependency_ids and id in dependency_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot depend on itself")

        if dependent_ids and id in dependent_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot depend on itself")

        if dependency_ids and dependent_ids:
            overlap = set(dependency_ids) & set(dependent_ids)
            if overlap:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task IDs {overlap} cannot be both dependencies and dependents")

        if dependency_ids:
            found = db.query(models.Task.id).filter(models.Task.id.in_(dependency_ids)).all()
            found_ids = {row.id for row in found}
            missing = set(dependency_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tasks with ids {missing} not found")

        if dependent_ids:
            found = db.query(models.Task.id).filter(models.Task.id.in_(dependent_ids)).all()
            found_ids = {row.id for row in found}
            missing = set(dependent_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tasks with ids {missing} not found")

        if dependency_ids:
            for dep_id in dependency_ids:
                db.add(models.TaskDependency(task_id=id, depends_on_task_id=dep_id))

        if dependent_ids:
            for dep_id in dependent_ids:
                db.add(models.TaskDependency(task_id=dep_id, depends_on_task_id=id))

        db.commit()
        db.refresh(task)

        return task
    
    except Exception:
        db.rollback()
        raise

@router.patch('/{id}', response_model=schemas.TaskResponse)
def update_task_partial(id: int, updated_task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"task with id: {id} not found")

    updated_task_data = updated_task.dict(exclude_unset=True)
    updated_task_data["user_id"] = 1  # ← hardcode for testing, remove when auth is wired in

    dependency_ids = updated_task_data.pop("dependencies", None)
    dependent_ids = updated_task_data.pop("dependents", None)

    if "course_id" in updated_task_data:
        if not db.query(models.Course).filter(models.Course.id == updated_task_data["course_id"]).first():
            raise HTTPException(status_code=404, detail="Course not found")

    if "assessment_id" in updated_task_data:
        assessment = (db.query(models.Assessment).join(models.AssessmentGroup).filter(models.Assessment.id == updated_task_data["assessment_id"]).first())
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # get the course_id to check against — either from the update or the existing task
        course_id_to_check = updated_task_data.get("course_id", task.course_id)

        if not course_id_to_check:
            raise HTTPException(status_code=400, detail="course_id is required when setting assessment_id")
        
        if assessment.assessment_group.course_id != course_id_to_check:
            raise HTTPException(status_code=400, detail="Assessment does not belong to the specified course")

    if "estimated_hours" in updated_task_data and updated_task_data["estimated_hours"] < 0:
        raise HTTPException(status_code=400, detail="estimated_hours must be positive")
    
    if "deadline" in updated_task_data and updated_task_data["deadline"] < date.today():
        raise HTTPException(status_code=400, detail="deadline cannot be in the past")

    if any(field in updated_task_data for field in ["deadline", "estimated_hours", "grade_impact", "course_id", "assessment_id"]):
        priority_data = {
            "deadline": updated_task_data.get("deadline", task.deadline),
            "estimated_hours": updated_task_data.get("estimated_hours", task.estimated_hours),
            "grade_impact": updated_task_data.get("grade_impact", task.grade_impact),
            "course_id": updated_task_data.get("course_id", task.course_id),
            "assessment_id": updated_task_data.get("assessment_id", task.assessment_id),
        }
        priority = get_priority(**priority_data)
        updated_task_data["priority"] = priority

    for field, value in updated_task_data.items():
        setattr(task, field, value)

    try:
        db.flush()

        if dependency_ids is not None:
            if id in dependency_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot depend on itself")

            if dependent_ids is not None:
                overlap = set(dependency_ids) & set(dependent_ids)
                if overlap:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task IDs {overlap} cannot be both dependencies and dependents")

            found = db.query(models.Task.id).filter(models.Task.id.in_(dependency_ids)).all()
            found_ids = {row.id for row in found}
            missing = set(dependency_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tasks with ids {missing} not found")

            db.query(models.TaskDependency).filter(models.TaskDependency.task_id == id).delete()
            for dep_id in dependency_ids:
                db.add(models.TaskDependency(task_id=id, depends_on_task_id=dep_id))

        if dependent_ids is not None:
            if id in dependent_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot depend on itself")

            found = db.query(models.Task.id).filter(models.Task.id.in_(dependent_ids)).all()
            found_ids = {row.id for row in found}
            missing = set(dependent_ids) - found_ids
            if missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tasks with ids {missing} not found")

            db.query(models.TaskDependency).filter(models.TaskDependency.depends_on_task_id == id).delete()
            for dep_id in dependent_ids:
                db.add(models.TaskDependency(task_id=dep_id, depends_on_task_id=id))

        db.commit()
        db.refresh(task)
        return task

    except Exception:
        db.rollback()
        raise

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    task = task_query.first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"task with id: {id} was not found")
    
    task_query.delete(synchronize_session=False)
    db.commit()
    





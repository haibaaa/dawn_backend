from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_
from app.models.models import Task, Enrollment, TaskDependency, Course
from app.enums import Status


class PriorityEngine:
    @staticmethod
    def calculate_task_priority(db: Session, task: Task) -> float:
    
        if not task or task.status == Status.COMPLETED:
            return 0.0

        # Check Dependencies
        blocking_tasks = (
        db.query(Task)
        .join(TaskDependency, Task.id == TaskDependency.depends_on_task_id)
        .filter(
            TaskDependency.task_id == task.id,
            Task.status != Status.COMPLETED
        )
        .first()
        )
        
        if blocking_tasks:
            return 0.0

        # Enrollment Logic (Safe access)
        # Assuming one enrollment per user per course
        enrollment = (
            db.query(Enrollment)
            .filter_by(user_id=task.user_id, course_id=task.course_id)
            .first()
        )

        target_gap = 10.0
        if enrollment and enrollment.target_score is not None:
            # logic: target - current
            target_gap = max(
                1.0, enrollment.target_score - (enrollment.current_score or 0.0)
            )

        # Urgency Calculation

        if not task.deadline:
            urgency = 5.0  # default urgency for tasks with no deadline
        else:
            task_date = task.deadline if isinstance(task.deadline, date) else task.deadline.date()
            days_until = (task_date - date.today()).days
            if days_until < 0:
                urgency = 20.0
            elif days_until == 0:
                urgency = 15.0
            else:
                urgency = 10.0 / (days_until + 1)

        # Formula
        impact = (task.grade_impact * 10) if task.grade_impact is not None else 1.0
        priority_score = (urgency * impact) * (target_gap / 10.0)
        
        # ROI Bonus
        if task.estimated_hours is not None and task.estimated_hours > 0:
            priority_score += 1.0 / task.estimated_hours

        return round(priority_score, 2)

    @staticmethod
    def update_all_priorities(db: Session, user_id: str):
        tasks = (
            db.query(Task)
            .filter(Task.user_id == user_id, Task.status != Status.COMPLETED)
            .all()
        )
        for task in tasks:
            task.priority = PriorityEngine.calculate_task_priority(db, task)
        db.commit()

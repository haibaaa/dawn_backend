from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Float, Date, Enum as SAEnum, DateTime
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from .database import Base
from .schemas import Status

class Enrollment(Base):
    __tablename__ = "enrollments"

    __table_args__ = (
    CheckConstraint("target_score >= 0 AND target_score <= 100", name="check_target_score"),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)

    grade = Column(String(2), nullable=True)
    final_score = Column(Float, nullable=True)
    current_score = Column(Float, nullable=True)
    
    target_grade = Column(String(2), nullable=True)
    target_score = Column(Float, nullable= True)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class StudentAssessment(Base):
    __tablename__ = "student_assessments"

    __table_args__ = (
    CheckConstraint("score >= 0", name="check_score_positive"),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True)

    score = Column(Float, nullable=True)

    user = relationship("User", back_populates="student_assessments")
    assessment = relationship("Assessment", back_populates="student_assessments")

class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    __table_args__ = (
        CheckConstraint("task_id != depends_on_task_id", name="check_no_self_dependency"),
    )

    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies_links")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id], back_populates="dependents_links")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    tasks = relationship("Task", back_populates="user")
    
    enrollments = relationship("Enrollment", back_populates="user")
    student_assessments = relationship("StudentAssessment", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint("estimated_hours >= 0", name="check_estimated_hours_positive"),
        CheckConstraint("priority >= 0", name="check_priority_positive")
    )
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    deadline = Column(Date, index=True)
    estimated_hours = Column(Float)
    grade_impact = Column(Float)
    status = Column(SAEnum(Status, name= "task_status_enum"), server_default='pending', nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), index=True)
    priority = Column(Float, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="tasks")

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    course = relationship("Course", back_populates="tasks")

    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True, index=True)
    assessment = relationship("Assessment", back_populates="tasks")

    dependencies_links = relationship("TaskDependency", foreign_keys=[TaskDependency.task_id], back_populates="task")
    dependents_links = relationship("TaskDependency", foreign_keys=[TaskDependency.depends_on_task_id], back_populates="depends_on_task")

    prerequisites = association_proxy("dependencies_links","depends_on_task", creator=lambda t: TaskDependency(depends_on_task=t))
    dependents = association_proxy("dependents_links","task", creator=lambda t: TaskDependency(task=t))

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    course_code = Column(String, nullable=False, unique=True, index=True)
    semester = Column(Integer) # might remove, conflicting case UWES
    a_cutoff = Column(Float)

    enrollments = relationship("Enrollment", back_populates="course")

    tasks = relationship("Task", back_populates="course")

    assessment_groups = relationship("AssessmentGroup", back_populates="course")

class AssessmentGroup(Base):
    __tablename__ = "assessment_groups"

    __table_args__ = (
        CheckConstraint("best_of <= count", name="check_best_of_less_than_count"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    best_of = Column(Integer)
    count = Column(Integer, nullable=False)

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    course = relationship("Course", back_populates="assessment_groups")

    assessments = relationship("Assessment", back_populates="assessment_group")

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    max_score = Column(Float) # might set nullable to true... want to account for case when the student doesn't know max score yet
    deadline = Column(DateTime(timezone=True))

    tasks = relationship("Task", back_populates="assessment")

    assessment_group_id = Column(Integer, ForeignKey("assessment_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_group = relationship("AssessmentGroup", back_populates="assessments")

    student_assessments = relationship("StudentAssessment", back_populates="assessment")





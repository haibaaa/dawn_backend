<<<<<<< HEAD
from typing import List, Literal, Optional
=======
from typing import Optional, Literal
>>>>>>> 60862b4a8f7b35ffec34c7a106471420f9c599ae
from pydantic import BaseModel, EmailStr, model_validator, ConfigDict, Field
from datetime import datetime, date
from app.enums import Status


# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Status = Status.PENDING
    deadline: Optional[date] = None
    estimated_hours: Optional[float] = None
    grade_impact: Optional[float] = None
    course_id: Optional[int] = None
    assessment_id: Optional[int] = None
    dependencies: Optional[list[int]] = None
    dependents: Optional[list[int]] = None


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    user_id: str
    priority: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def extract_dependency_ids(cls, data):
        if not isinstance(data, dict):
            deps = getattr(data, "prerequisites", []) or []
            dependents = getattr(data, "dependents", []) or []
            return {
                **data.__dict__,
                "dependencies": [t.id for t in deps],
                "dependents": [t.id for t in dependents],
            }
        return data


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    deadline: Optional[date] = None
    estimated_hours: Optional[float] = None
    grade_impact: Optional[float] = None
    course_id: Optional[int] = None
    assessment_id: Optional[int] = None
    dependencies: Optional[list[int]] = None
    dependents: Optional[list[int]] = None


class TaskStatusUpdate(BaseModel):
    status: Status


# ---- QUIZ SCHEMA ----
class QuizQuestion(BaseModel):
    type: Literal["quiz"]  # Hardcoded type for the UI to read
    question: str
    correct_answer: str
    options: list[str]  # List of 4 multiple choice options (including correct one)
    explanation: str  # Why the answer is correct


class QuizResponse(BaseModel):
    title: str  # e.g., "Quiz based on Molecular_Bio_Lec2.pdf"
    questions: list[QuizQuestion]


# --- ASSESSMENT SCHEMAS ---
class AssessmentOut(BaseModel):
    id: int
    name: str
    max_score: Optional[float] = None
    deadline: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AssessmentGroupOut(BaseModel):
    id: int
    name: str
    weight: float
    count: int
    best_of: Optional[int] = None
    assessments: list[AssessmentOut] = []
    model_config = ConfigDict(from_attributes=True)


class AssessmentGroupCreate(BaseModel):
    name: str
    weight: float
    count: int
    best_of: Optional[int] = None
    course_code: str


class AssessmentGroupUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    count: Optional[int] = None
    best_of: Optional[int] = None


class AssessmentCreate(BaseModel):
    name: str
    max_score: Optional[float] = None
    deadline: Optional[datetime] = None
    assessment_group_id: int


class AssessmentUpdate(BaseModel):
    name: Optional[str] = None
    max_score: Optional[float] = None
    deadline: Optional[datetime] = None


# --- COURSE SCHEMAS ---
class CourseOut(BaseModel):
    id: int
    name: str
    course_code: str
    semester: Optional[int] = None
    a_cutoff: Optional[float] = None
    assessment_groups: list[AssessmentGroupOut] = []
    model_config = ConfigDict(from_attributes=True)


class CourseCreate(BaseModel):
    name: str
    course_code: str
    semester: Optional[int] = None
    a_cutoff: Optional[float] = None


# --- ENROLLMENT SCHEMAS ---
class EnrollmentOut(BaseModel):
    grade: Optional[str] = None
    final_score: Optional[float] = None
    current_score: Optional[float] = None
    target_grade: Optional[str] = None
    target_score: Optional[float] = None
    course: CourseOut
    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    course_code: str
    target_grade: Optional[str] = None
    target_score: Optional[float] = None


class EnrollmentUpdate(BaseModel):
    target_grade: Optional[str] = None
    target_score: Optional[float] = None


# --- STUDENT ASSESSMENT SCHEMAS ---
class StudentAssessmentCreate(BaseModel):
    assessment_id: int
    score: Optional[float] = None


class StudentAssessmentUpdate(BaseModel):
    score: Optional[float] = None


class StudentAssessmentOut(BaseModel):
    score: Optional[float] = None
    assessment: AssessmentOut
    model_config = ConfigDict(from_attributes=True)


# --- FLASHCARD SCHEMAS ---
class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardResponse(BaseModel):
    flashcards: list[Flashcard]


# --- RESOURCE SCHEMAS ---
class ResourceCreate(BaseModel):
    title: str
    course_id: Optional[int] = None
    tags: str


class ResourceResponse(BaseModel):
    id: int
    title: str
    file_url: str
    tags: list[str]
    user_id: str
    model_config = ConfigDict(from_attributes=True)

<<<<<<< HEAD

class QuizQuestion(BaseModel):
    type: Literal["quiz"] # Hardcoded type for the UI to read
    question: str
    correct_answer: str
    options: List[str] # List of 4 multiple choice options (including correct one)
    explanation: str # Why the answer is correct
    options: list[str]  # List of 4 multiple choice options (including correct one)
    explanation: str  # Why the answer is correct


class QuizResponse(BaseModel):
    title: str 
    questions: List[QuizQuestion]
    title: str
    questions: list[QuizQuestion]
=======
>>>>>>> 60862b4a8f7b35ffec34c7a106471420f9c599ae

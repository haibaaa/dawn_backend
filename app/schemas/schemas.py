from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime, date
from enum import Enum


# --- ENUMS ---
class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# --- USER SCHEMAS ---


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str  # Matches Supabase UUID string
    model_config = ConfigDict(from_attributes=True)


# --- COURSE SCHEMAS ---
class CourseBase(BaseModel):
    name: str
    course_code: str
    semester: int | None = None
    a_cutoff: float | None = 80.0


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- ASSESSMENT SCHEMAS ---
class AssessmentGroupBase(BaseModel):
    name: str
    weight: float
    best_of: int | None = None
    count: int
    course_id: int


class AssessmentBase(BaseModel):
    name: str
    max_score: float | None = None
    deadline: datetime | None = None
    assessment_group_id: int


class AssessmentResponse(AssessmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    title: str
    description: str | None = None
    deadline: date | None = None
    estimated_hours: float = Field(default=0.0, ge=0)
    grade_impact: float | None = None
    status: Status = Status.PENDING
    priority: float = Field(default=0.0, ge=0)
    course_id: int | None = None
    assessment_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: date | None = None
    estimated_hours: float | None = Field(None, ge=0)
    status: Status | None = None
    priority: float | None = Field(None, ge=0)


class TaskResponse(TaskBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- ENROLLMENT SCHEMAS ---
class EnrollmentBase(BaseModel):
    course_id: int
    grade: str | None = Field(None, max_length=2)
    current_score: float | None = None
    target_score: float = Field(default=0.0, ge=0, le=100)


class EnrollmentResponse(EnrollmentBase):
    user_id: str
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
    course_id: int | None = None
    tags: str  # We'll receive tags as a comma-separated string from the Form


class ResourceResponse(BaseModel):
    id: int
    title: str
    file_url: str
    tags: list[str]
    user_id: str
    model_config = ConfigDict(from_attributes=True)

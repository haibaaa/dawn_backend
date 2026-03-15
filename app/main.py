from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from contextlib import asynccontextmanager
import pandas as pd
from app.core.database import engine, Base
from app.utils import valid_courses
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    auth,
    flashcard,
    resources,
    quiz,
    tasks,
    enrollment,
    courses,
    assessment_groups,
    assessments,
    student_assessments,
)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    df = pd.read_excel("courses.xlsx")
    df["Course Code"] = df["Course Code"].str.split("/").str[0].str.strip()
    valid_courses.update(dict(zip(df["Course Code"], df["Course Name"])))
    yield


app = FastAPI(lifespan=lifespan)


# enable cors for the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(flashcard.router, prefix="/flashcards", tags=["Flashcards"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(enrollment.router, prefix="/enrollments", tags=["Enrollments"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(
    assessment_groups.router, prefix="/assessment-groups", tags=["Assessment Groups"]
)
app.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])
app.include_router(
    student_assessments.router,
    prefix="/student-assessments",
    tags=["Student Assessments"],
)
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected to supabase"}


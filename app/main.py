from fastapi import FastAPI
from app.core.database import engine, Base
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

# Create tables in Supabase (Postgres)
Base.metadata.create_all(bind=engine)

app = FastAPI()


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
app.include_router(enrollment.router, prefix="/enrollments", tags=["Tasks"])
app.include_router(courses.router, prefix="/courses", tags=["Tasks"])
app.include_router(
    assessment_groups.router, prefix="/assessment-groups", tags=["Tasks"]
)
app.include_router(assessments.router, prefix="/assessments", tags=["Tasks"])
app.include_router(
    student_assessments.router, prefix="/student-assessments", tags=["Tasks"]
)
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected to supabase"}

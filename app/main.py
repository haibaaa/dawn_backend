from fastapi import FastAPI
from app.core.database import engine, Base
from app.routes import auth, flashcard, resources, quiz, tasks, enrollment, courses, assessment_groups, assessments, student_assessments

# Create tables in Supabase (Postgres)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(flashcard.router, prefix="/flashcards", tags=["Flashcards"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(enrollment.router, prefix="/enrollments", tags=["Tasks"])
app.include_router(courses.router, prefix="/courses", tags=["Tasks"])
app.include_router(assessment_groups.router, prefix="/assessment-groups", tags=["Tasks"])
app.include_router(assessments.router, prefix="/assessments", tags=["Tasks"])
app.include_router(student_assessments.router, prefix="/student-assessments", tags=["Tasks"])
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected to supabase"}

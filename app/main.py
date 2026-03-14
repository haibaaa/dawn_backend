from fastapi import FastAPI
from app.core.database import engine, Base
from app.routes import auth, flashcard, resources, quiz, tasks

# Create tables in Supabase (Postgres)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(flashcard.router, prefix="/flashcards", tags=["Flashcards"])
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(quiz.router, prefix="/quiz", tags=["Tasks"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected to supabase"}

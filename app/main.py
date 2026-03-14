from fastapi import FastAPI
from app.core.database import engine, Base
from app.routes import auth, tasks, flashcard

# Import models here so Base knows about them
from app.models import models

# Create tables in Supabase (Postgres)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(flashcard.router, prefix="/api/flashcards", tags=["Flashcards"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected to supabase"}

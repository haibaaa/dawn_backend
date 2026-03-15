from fastapi import FastAPI
from app.core.database import engine, Base
from app.routes import auth, flashcard, resources, quiz, tasks
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected to supabase"}

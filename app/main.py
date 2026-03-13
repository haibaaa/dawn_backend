from fastapi import FastAPI

# from app.routes import tasks, grades

app = FastAPI()

# app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
# app.include_router(grades.router, prefix="/grades", tags=["Grades"])


@app.get("/")
def health_check():
    return {"status": "online"}

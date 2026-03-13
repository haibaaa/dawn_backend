from fastapi import APIRouter, Depends
from appwrite.services.databases import Databases
from app.auth import get_user_client
import os

router = APIRouter()


# this is an example path --> it will not compile
# basically use the depends clause
@router.get("/")
async def get_my_tasks(user_client=Depends(get_user_client)):
    db = Databases(user_client)
    # This will only return tasks the user has permissions for
    tasks = db.list_documents(
        database_id=os.getenv("APPWRITE_DB_ID"),
        collection_id=os.getenv("APPWRITE_TASK_COLLECTION"),
    )
    return tasks

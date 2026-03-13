from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.account import Account
from appwrite.id import ID
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


# 1. Admin Client (Uses API Key) - For creating users
def get_admin_client():
    return (
        Client()
        .set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
        .set_project(os.getenv("APPWRITE_PROJECT_ID"))
        .set_key(os.getenv("APPWRITE_API_KEY"))
    )


# 2. Public Client (No API Key) - For logging in
def get_public_client():
    return (
        Client()
        .set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
        .set_project(os.getenv("APPWRITE_PROJECT_ID"))
    )


class UserAuth(BaseModel):
    email: EmailStr
    password: str


@app.post("/test/signup")
async def signup(user: UserAuth):
    client = get_admin_client()
    users = Users(client)
    try:
        # This creates a user in the Appwrite Auth Console
        result = users.create(
            user_id=ID.unique(),
            email=user.email,
            password=user.password,
        )
        return {
            "message": "Success!",
            "user_id": result["$id"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@app.post("/test/login")
async def login(user: UserAuth):
    client = get_admin_client()  # Needs API Key to create JWT on behalf of user
    account = Account(client)
    try:
        # Step A: Authenticate the user
        account.create_email_password_session(
            user.email,
            user.password,
        )
        # Step B: Generate the 15-minute token
        jwt_response = account.create_jwt()

        return {
            "token": jwt_response["jwt"],
            "status": "Logged In",
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

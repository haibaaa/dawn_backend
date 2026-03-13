from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from appwrite.services.users import Users
from appwrite.services.account import Account
from appwrite.id import ID
from app.config import get_admin_client, get_base_client

router = APIRouter()


# models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup(user: SignupRequest):
    """Creates a new student account in Appwrite."""
    client = get_admin_client()
    users = Users(client)
    try:
        result = users.create(
            user_id=ID.unique(),
            email=user.email,
            password=user.password,
        )
        return {"status": "User created", "user_id": result["$id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user: LoginRequest):
    """Logs in and returns a JWT for subsequent requests."""
    client = get_base_client()  # Sessions are created on the base client
    account = Account(client)
    try:
        # 1. Create the session
        account.create_email_password_session(user.email, user.password)

        # 2. Generate JWT
        jwt_res = account.create_jwt()

        return {"token": jwt_res["jwt"], "status": "Logged In", "type": "Bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials or " + str(e))

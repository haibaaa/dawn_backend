from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from app.core.config import settings
from app.schemas.schemas import UserCreate

router = APIRouter()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@router.post("/signup")
async def signup(
    user_data: UserCreate,
):  # FastAPI now knows to look in the Request Body
    # Access them via user_data.email and user_data.password
    response = supabase.auth.sign_up(
        {
            "email": user_data.email,
            "password": user_data.password,
        }
    )
    if response.user is None:
        raise HTTPException(
            status_code=400,
            detail="signup failed. the user might already exist or the request was invalid.",
        )

    return {
        "message": "success! check your email for confirmation.",
        "user_id": response.user.id,
    }


@router.post("/login")
async def login(
    user_data: UserCreate,
):
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": user_data.email,
                "password": user_data.password,
            }
        )
        if response.session is None:
            raise HTTPException(
                status_code=400,
                detail="wrong credentials",
            )
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

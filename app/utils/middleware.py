from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from app.core.config import settings

# this tells fastapi where to look for the token (the 'lock')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY,
)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # we ask supabase: "is this jwt valid?"
        user_res = supabase.auth.get_user(
            token,
        )

        return user_res.user  # returns the full supabase user object
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="could not validate credentials",
        )

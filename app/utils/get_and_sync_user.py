from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from supabase import create_client, Client
from app.core.config import settings
from app.core.database import get_db
from app.models import User

# this looks for the "authorization: bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


async def get_and_sync_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    # validate token with supabase
    try:
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or expired session",
            )

        auth_user = user_res.user
        user_id = auth_user.id
        user_email = auth_user.email

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"authentication failed: {str(e)}",
        )

    # check/sync with local db
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        # first time this user has hit our api
        db_user = User(id=user_id, email=user_email)
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="failed to sync user to local database",
            )

    return db_user

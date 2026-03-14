from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.models import User
from app.core.database import get_db


async def get_and_sync_user(db: Session = Depends(get_db)):
    # 1. In a real scenario, you'd decode the JWT from the header here.
    # For now, we'll use your current test ID.
    user_id = "79e049e6-ac6e-488d-a359-5f6cc8dd6b2f"
    user_email = "haiba@nixos.local"  # Mocking email for now

    # 2. Check the PUBLIC schema
    db_user = db.query(User).filter(User.id == user_id).first()

    # 3. If they don't exist in 'public', create them now
    if not db_user:
        print(f"DEBUG: Syncing user {user_id} to public schema...")
        db_user = User(id=user_id, email=user_email)
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
        except Exception as e:
            db.rollback()
            # This will tell us EXACTLY why the DB rejected the user
            raise HTTPException(
                status_code=500,
                detail=f"User sync failed: {str(e)}",
            )

    return db_user

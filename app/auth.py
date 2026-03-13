from fastapi import Header, HTTPException, Depends
from appwrite.client import Client
from .config import get_admin_client


async def get_user_client(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Token")

    token = authorization.split(" ")[1]
    client = Client()
    # ... setup endpoint and project ...
    client.set_jwt(token)
    return client

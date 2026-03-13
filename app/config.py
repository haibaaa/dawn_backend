import os
from appwrite.client import Client
from dotenv import load_dotenv

load_dotenv()


def get_base_client():
    """Returns a client with project and endpoint set."""
    return (
        Client()
        .set_endpoint(os.getenv("APPWRITE_ENDPOINT", ""))
        .set_project(os.getenv("APPWRITE_PROJECT_ID", ""))
    )


def get_admin_client():
    """Returns a client with full API Key permissions."""
    client = get_base_client()
    return client.set_key(os.getenv("APPWRITE_API_KEY", ""))

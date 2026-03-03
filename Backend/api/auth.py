from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("API_KEY", "")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Validate the X-API-Key header against the configured API_KEY."""
    if not API_KEY:
        # If no API_KEY is configured, skip auth (dev convenience)
        return None
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

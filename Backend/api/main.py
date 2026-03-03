from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.routes import tasks, analytics
from api.auth import verify_api_key
from database.db import init_db
import os

init_db()

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="Smart Planner API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers (protected by API key) ---
app.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(verify_api_key)],
)

@app.get("/")
def root():
    """Health check — no auth required."""
    return {"status": "smart-planner api is running"}
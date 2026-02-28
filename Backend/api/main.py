from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import tasks, analytics
from database.db import init_db

init_db()

app = FastAPI(title="Smart Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

@app.get("/")
def root():
    return {"status": "smart-planner api is running"}
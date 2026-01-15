from fastapi import APIRouter
from db import db
from datetime import datetime

router = APIRouter(prefix="/generate")

@router.post("/")
async def generate_script(payload: dict):
    job = {
        "source": "api",
        "article_text": payload["text"],
        "status": "queued",
        "email_sent": False,
        "created_at": datetime.now()
    }
    result = db["jobs"].insert_one(job)
    return {"job_id": str(result.inserted_id)}

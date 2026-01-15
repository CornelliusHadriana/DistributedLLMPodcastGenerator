"""
POST /ingest endpoint - accepts article data and enqueues normalization job.
"""

from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from api.schemas.requests import IngestRequest, IngestResponse
from db import db
from config.redis_config import normalize_queue

router = APIRouter()


def normalize_article_job(article_id: str):
    """
    Placeholder function for normalization job.
    
    This will be implemented by the Normalizer service worker.
    For now, it's just a placeholder to enqueue the job.
    
    Args:
        article_id: ID of the article to normalize
    """
    # This function will be called by the RQ worker
    # Actual implementation will be in the Normalizer service
    pass


@router.post("/ingest", response_model=IngestResponse)
async def ingest_article(request: IngestRequest):
    """
    Ingest an article and enqueue a normalization job.
    
    This endpoint:
    1. Stores the raw article data in MongoDB
    2. Creates an article document with status 'ingested'
    3. Enqueues a normalization job to the normalize queue
    4. Returns the article_id
    
    No heavy processing is done here - all work is delegated to workers.
    """
    try:
        # Create article document
        article_doc = {
            "title": request.title,
            "url": request.url,
            "raw_text": request.raw_text,
            "source": request.source,
            "status": "ingested",
            "pipeline_status": {
                "normalize": "pending",
                "summarize": "pending",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insert article into database
        result = db.articles.insert_one(article_doc)
        article_id = str(result.inserted_id)
        
        # Enqueue normalization job
        # Note: The normalize job function will be implemented by the Normalizer service
        # For now, we enqueue with article_id as the argument
        normalize_queue.enqueue(
            normalize_article_job,
            article_id,
            job_id=f"normalize_{article_id}",
            job_timeout=600  # 10 minutes timeout
        )
        
        return IngestResponse(
            article_id=article_id,
            status="ingested",
            message="Article ingested and normalization job enqueued"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest article: {str(e)}"
        )

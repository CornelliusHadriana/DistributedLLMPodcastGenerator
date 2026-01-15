"""
GET /episode/{article_id} endpoint - returns final script and audio URL.
"""

from fastapi import APIRouter, HTTPException
from bson import ObjectId
from api.schemas.requests import EpisodeResponse
from db import db

router = APIRouter()


@router.get("/episode/{article_id}", response_model=EpisodeResponse)
async def get_episode(article_id: str):
    """
    Get the final episode data (script and audio URL) for an article.
    
    This endpoint:
    1. Retrieves the article from MongoDB
    2. Extracts the final script and audio URL
    3. Returns the episode data
    
    Only reads from database - no processing.
    """
    try:
        # Validate ObjectId format
        try:
            article_object_id = ObjectId(article_id)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid article_id format: {article_id}"
            )
        
        # Get article from database
        article = db.articles.find_one({"_id": article_object_id})
        
        if not article:
            raise HTTPException(
                status_code=404,
                detail=f"Article not found: {article_id}"
            )
        
        # Extract episode data
        script = article.get("script")
        audio_url = article.get("audio_url")
        status = article.get("status", "unknown")
        published_at = article.get("published_at")
        
        # Check if episode is ready (has script and audio)
        if script and audio_url:
            episode_status = "published"
        elif script:
            episode_status = "script_ready"
        else:
            episode_status = status
        
        return EpisodeResponse(
            article_id=article_id,
            script=script,
            audio_url=audio_url,
            status=episode_status,
            published_at=published_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get episode: {str(e)}"
        )

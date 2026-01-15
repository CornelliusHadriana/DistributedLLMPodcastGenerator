"""
GET /status/{article_id} endpoint - returns current pipeline status.
"""

from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from api.schemas.requests import StatusResponse, PipelineStatus
from db import db

router = APIRouter()


def get_overall_status(pipeline_status: dict) -> str:
    """
    Determine overall pipeline status from individual stage statuses.
    
    Args:
        pipeline_status: Dictionary with stage statuses
        
    Returns:
        Overall status: 'completed', 'in_progress', 'failed', or 'pending'
    """
    stages = list(pipeline_status.values())
    
    if all(status == "completed" for status in stages):
        return "completed"
    elif any(status == "failed" for status in stages):
        return "failed"
    elif any(status in ["running", "completed"] for status in stages):
        return "in_progress"
    else:
        return "pending"


@router.get("/status/{article_id}", response_model=StatusResponse)
async def get_status(article_id: str):
    """
    Get the current pipeline status for an article.
    
    This endpoint:
    1. Retrieves the article from MongoDB
    2. Extracts pipeline status for each stage
    3. Returns structured status information
    
    No heavy processing - only database reads.
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
        
        # Extract pipeline status
        pipeline_status = article.get("pipeline_status", {})
        
        # Build stage status list
        stage_statuses = [
            PipelineStatus(
                stage="normalize",
                status=pipeline_status.get("normalize", "pending"),
                updated_at=pipeline_status.get("normalize_updated_at")
            ),
            PipelineStatus(
                stage="summarize",
                status=pipeline_status.get("summarize", "pending"),
                updated_at=pipeline_status.get("summarize_updated_at")
            ),
            PipelineStatus(
                stage="assemble",
                status=pipeline_status.get("assemble", "pending"),
                updated_at=pipeline_status.get("assemble_updated_at")
            ),
            PipelineStatus(
                stage="text_to_speech",
                status=pipeline_status.get("text_to_speech", "pending"),
                updated_at=pipeline_status.get("text_to_speech_updated_at")
            ),
            PipelineStatus(
                stage="publish",
                status=pipeline_status.get("publish", "pending"),
                updated_at=pipeline_status.get("publish_updated_at")
            )
        ]
        
        # Determine overall status
        overall_status = get_overall_status(pipeline_status)
        
        return StatusResponse(
            article_id=article_id,
            overall_status=overall_status,
            stages=stage_statuses,
            created_at=article.get("created_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

"""
Pydantic schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IngestRequest(BaseModel):
    """Request schema for POST /ingest endpoint."""
    title: Optional[str] = Field(None, description="Article title")
    url: Optional[str] = Field(None, description="Article URL")
    raw_text: str = Field(..., description="Raw article text to process")
    source: Optional[str] = Field(None, description="Source of the article (e.g., newsletter name)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Example Article",
                "url": "https://example.com/article",
                "raw_text": "This is the full article text...",
                "source": "TLDR Newsletter"
            }
        }


class IngestResponse(BaseModel):
    """Response schema for POST /ingest endpoint."""
    article_id: str = Field(..., description="Unique identifier for the article")
    status: str = Field(..., description="Initial status of the article")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "507f1f77bcf86cd799439011",
                "status": "ingested",
                "message": "Article ingested and normalization job enqueued"
            }
        }


class PipelineStatus(BaseModel):
    """Status of each pipeline stage."""
    stage: str = Field(..., description="Pipeline stage name")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stage": "normalize",
                "status": "completed",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class StatusResponse(BaseModel):
    """Response schema for GET /status/{article_id} endpoint."""
    article_id: str = Field(..., description="Article identifier")
    overall_status: str = Field(..., description="Overall pipeline status")
    stages: list[PipelineStatus] = Field(..., description="Status of each pipeline stage")
    created_at: Optional[datetime] = Field(None, description="Article creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "507f1f77bcf86cd799439011",
                "overall_status": "in_progress",
                "stages": [
                    {"stage": "normalize", "status": "completed", "updated_at": "2024-01-15T10:30:00"},
                    {"stage": "summarize", "status": "running", "updated_at": "2024-01-15T10:35:00"},
                    {"stage": "assemble", "status": "pending", "updated_at": None},
                    {"stage": "text_to_speech", "status": "pending", "updated_at": None},
                    {"stage": "publish", "status": "pending", "updated_at": None}
                ],
                "created_at": "2024-01-15T10:25:00"
            }
        }


class EpisodeResponse(BaseModel):
    """Response schema for GET /episode/{article_id} endpoint."""
    article_id: str = Field(..., description="Article identifier")
    script: Optional[str] = Field(None, description="Final podcast script")
    audio_url: Optional[str] = Field(None, description="URL to the generated audio file")
    status: str = Field(..., description="Current status")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "507f1f77bcf86cd799439011",
                "script": "Welcome to today's episode...",
                "audio_url": "https://storage.example.com/episodes/episode_123.mp3",
                "status": "published",
                "published_at": "2024-01-15T11:00:00"
            }
        }

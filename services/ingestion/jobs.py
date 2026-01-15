"""
Job definitions for the ingestion service.

This module contains functions that will be executed by RQ workers
for processing email ingestion tasks.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from auth.gmail_auth import get_gmail_service
from services.ingestion.fetch_emails import get_latest_newsletter_text
from db import db


def process_email_ingestion(sender: str, subject: str = None) -> str:
    """
    Process email ingestion job.
    
    Fetches emails from the specified sender and creates LLM jobs
    for each newsletter text found.
    
    Args:
        sender: Email address of the sender (e.g., 'dan@tldrnewsletter.com')
        subject: Optional subject filter
        
    Returns:
        job_id: ID of the ingestion job created in the database
    """
    job_id = str(uuid.uuid4())
    
    # Create ingestion job record
    ingestion_job = {
        "job_id": job_id,
        "type": "ingestion",
        "source": {
            "type": "gmail",
            "sender": sender,
            "subject": subject
        },
        "status": "running",
        "metrics": {
            "created_at": datetime.now(),
            "started_at": datetime.now()
        },
        "error": None
    }
    
    try:
        # Insert job record
        db.jobs.insert_one(ingestion_job)
        
        # Fetch emails
        gmail_service = get_gmail_service()
        texts = get_latest_newsletter_text(gmail_service, sender)
        
        # TODO: Update to match new architecture
        # In the new architecture, ingestion should:
        # 1. Store raw article text in MongoDB
        # 2. Queue normalize jobs (not LLM jobs)
        # 
        # This code is temporarily kept but needs refactoring for:
        # - ingest_article queue → Normalizer service
        
        article_ids = []
        for text in texts:
            # Store article in database (temporary - needs proper article model)
            article_doc = {
                "raw_text": text,
                "sender": sender,
                "subject": subject or "Newsletter",
                "status": "ingested",
                "created_at": datetime.now()
            }
            result = db.articles.insert_one(article_doc)
            article_ids.append(str(result.inserted_id))
            
            # TODO: Queue normalize job instead of LLM job
            # from config.redis_config import ingest_article_queue
            # ingest_article_queue.enqueue(...)
        
        # Update ingestion job status
        db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "metrics.completed_at": datetime.now(),
                "output.llm_jobs_created": llm_job_ids
            }}
        )
        
        return job_id
        
    except Exception as e:
        # Update job with error
        db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "metrics.completed_at": datetime.now()
            }}
        )
        raise


def fetch_and_queue_newsletters(sender: str, subject: str = None) -> Dict[str, Any]:
    """
    Fetch newsletters and queue them for processing.
    
    This is a wrapper function that fetches newsletters and creates
    ingestion jobs for each one.
    
    Args:
        sender: Email address of the sender
        subject: Optional subject filter
        
    Returns:
        Dictionary with job_id and number of newsletters found
    """
    job_id = process_email_ingestion(sender, subject)
    return {
        "job_id": job_id,
        "status": "queued"
    }

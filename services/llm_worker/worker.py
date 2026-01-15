"""
Worker functions for LLM service.

NOTE: This file is outdated and needs to be refactored to match the new architecture.
The new architecture uses separate services: Normalizer, Summarization, and Assembly.

This module is kept temporarily but should be replaced with the new service-based approach.
"""

import time
from db import db


def worker_loop():
    """
    Legacy worker loop - DEPRECATED.
    
    This function is kept for backward compatibility but is no longer
    aligned with the new service-based architecture.
    
    TODO: Replace with Normalizer, Summarization, and Assembly services.
    """
    print("WARNING: This worker loop is deprecated.")
    print("Please use the new service-based architecture instead.")
    while True:
        # Legacy polling - will be replaced with RQ workers
        time.sleep(5)
        print("Worker loop running (deprecated - no jobs processed)")


def process_llm_job(job):
    """
    Legacy function - DEPRECATED.
    
    TODO: Replace with new service-based job processing.
    """
    raise NotImplementedError(
        "This function is deprecated. "
        "Please use the new service-based architecture with Normalizer, "
        "Summarization, and Assembly services."
    )
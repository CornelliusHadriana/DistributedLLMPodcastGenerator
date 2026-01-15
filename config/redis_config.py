"""
Redis configuration and queue definitions for all services.

This module provides:
- Redis connection setup
- Queue definitions for each service
- Helper functions for queue management
"""

import os
import redis
from rq import Queue
from dotenv import load_dotenv

load_dotenv()

# Redis connection configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Create Redis connection
redis_conn = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=False  # RQ expects bytes
)

# Queue definitions for the new service-based architecture
INGEST_ARTICLE_QUEUE_NAME = 'ingest_article'
NORMALIZE_QUEUE_NAME = 'normalize'
SUMMARIZE_CHUNKS_QUEUE_NAME = 'summarize_chunks'
ASSEMBLE_SUMMARY_QUEUE_NAME = 'assemble_summary'
TEXT_TO_SPEECH_QUEUE_NAME = 'text_to_speech'
PUBLISH_EPISODE_QUEUE_NAME = 'publish_episode'

# Legacy queues (deprecated, to be removed)
INGESTION_QUEUE_NAME = 'ingestion'
LLM_QUEUE_NAME = 'llm'

# Create queue instances for new architecture
ingest_article_queue = Queue(INGEST_ARTICLE_QUEUE_NAME, connection=redis_conn)
normalize_queue = Queue(NORMALIZE_QUEUE_NAME, connection=redis_conn)
summarize_chunks_queue = Queue(SUMMARIZE_CHUNKS_QUEUE_NAME, connection=redis_conn)
assemble_summary_queue = Queue(ASSEMBLE_SUMMARY_QUEUE_NAME, connection=redis_conn)
text_to_speech_queue = Queue(TEXT_TO_SPEECH_QUEUE_NAME, connection=redis_conn)
publish_episode_queue = Queue(PUBLISH_EPISODE_QUEUE_NAME, connection=redis_conn)

# Legacy queues (deprecated)
ingestion_queue = Queue(INGESTION_QUEUE_NAME, connection=redis_conn)
llm_queue = Queue(LLM_QUEUE_NAME, connection=redis_conn)

# All queues (for worker management)
ALL_QUEUES = {
    INGEST_ARTICLE_QUEUE_NAME: ingest_article_queue,
    NORMALIZE_QUEUE_NAME: normalize_queue,
    SUMMARIZE_CHUNKS_QUEUE_NAME: summarize_chunks_queue,
    ASSEMBLE_SUMMARY_QUEUE_NAME: assemble_summary_queue,
    TEXT_TO_SPEECH_QUEUE_NAME: text_to_speech_queue,
    PUBLISH_EPISODE_QUEUE_NAME: publish_episode_queue,
    # Legacy queues
    INGESTION_QUEUE_NAME: ingestion_queue,
    LLM_QUEUE_NAME: llm_queue,
}


def get_queue(queue_name: str) -> Queue:
    """
    Get a queue by name.
    
    Args:
        queue_name: Name of the queue
        
    Returns:
        Queue instance
        
    Raises:
        ValueError: If queue_name is not found
    """
    if queue_name not in ALL_QUEUES:
        raise ValueError(f"Unknown queue name: {queue_name}. Available queues: {list(ALL_QUEUES.keys())}")
    return ALL_QUEUES[queue_name]


def test_redis_connection() -> bool:
    """
    Test Redis connection.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        redis_conn.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

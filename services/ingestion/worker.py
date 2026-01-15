"""
RQ Worker for ingestion service.

Run this with: rq worker ingestion --path /path/to/project
Or use the run_worker.sh script.
"""

from rq import Worker, Connection
from config.redis_config import redis_conn, ingestion_queue


def start_worker():
    """Start RQ worker for ingestion queue."""
    with Connection(redis_conn):
        worker = Worker([ingestion_queue])
        worker.work()


if __name__ == '__main__':
    start_worker()

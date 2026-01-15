"""
Utility script to check Redis connection and queue status.

Usage:
    python -m utils.queue_status
"""

from config.redis_config import (
    redis_conn,
    ingestion_queue,
    llm_queue,
    test_redis_connection,
    ALL_QUEUES
)


def print_queue_status():
    """Print status of all queues."""
    print("=" * 60)
    print("Redis Queue Status")
    print("=" * 60)
    
    # Test Redis connection
    print("\n1. Redis Connection:")
    if test_redis_connection():
        print("   ✓ Redis is connected")
        print(f"   Host: {redis_conn.connection_pool.connection_kwargs.get('host', 'localhost')}")
        print(f"   Port: {redis_conn.connection_pool.connection_kwargs.get('port', 6379)}")
    else:
        print("   ✗ Redis connection failed")
        return
    
    # Queue status
    print("\n2. Queue Status:")
    print("-" * 60)
    
    for queue_name, queue in ALL_QUEUES.items():
        print(f"\n   Queue: {queue_name}")
        try:
            job_count = len(queue)
            failed_count = len(queue.failed_job_registry)
            started_count = len(queue.started_job_registry)
            finished_count = len(queue.finished_job_registry)
            
            print(f"   - Queued jobs: {job_count}")
            print(f"   - Started jobs: {started_count}")
            print(f"   - Finished jobs: {finished_count}")
            print(f"   - Failed jobs: {failed_count}")
            
            # Show next job if available
            if job_count > 0:
                job = queue.job_ids[0] if queue.job_ids else None
                if job:
                    print(f"   - Next job ID: {job}")
        except Exception as e:
            print(f"   ✗ Error getting queue status: {e}")
    
    print("\n" + "=" * 60)
    print("\nTo start workers, run:")
    print("  ./run_workers.sh")
    print("\nTo view detailed queue info:")
    print("  rq info")


if __name__ == "__main__":
    print_queue_status()

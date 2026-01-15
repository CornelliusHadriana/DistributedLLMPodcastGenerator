import time
from config.redis_config import ingestion_queue
from services.ingestion.jobs import process_email_ingestion

def run_ingestion_loop(sender: str = "dan@tldrnewsletter.com", interval: int = 300):
    """
    Run ingestion loop that queues email ingestion jobs.
    
    Args:
        sender: Email address to fetch newsletters from
        interval: Time in seconds between ingestion cycles
    """
    while True:
        try:
            # Queue ingestion job
            job = ingestion_queue.enqueue(
                process_email_ingestion,
                sender,
                job_id=f"ingestion_{int(time.time())}"
            )
            print(f"Queued ingestion job: {job.id}")
        except Exception as e:
            print(f"Error queuing ingestion job: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    run_ingestion_loop()
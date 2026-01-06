import time
from db import db
from datetime import datetime
from model import load_model
from generation import generate_script

def worker_loop():
    while True:
        job = db.jobs.find_one({"status": "queued"})
        if job:
            process_job(job)
        else:
            time.sleep(1)

def process_job(job):
    model, tokenizer = load_model()
    start = time.time()

    db.jobs.update_one(
        {"job_id": job["job_id"]},
        {"$set": {
            "status": "running",
            "metrics.started_at": datetime.now()
        }}
    )

    try:
        script = generate_script(
            job["input"]["article_text"],
            model,
            tokenizer
        )
        latency = time.time() - start

        db.jobs.update_one(
            {"job_id": job["job_id"]},
            {"$set": {
                "status": "completed",
                "output.script": script,
                "metrics.completed_at": datetime.now(),
                "metrics.latency_sec": latency
            }}
        )
    except Exception as e:
        db.jobs.update_one(
            {"job_id": job["job_id"]},
            {"$set": {
                "status": "failed",
                "error": str(e)
            }}
        )
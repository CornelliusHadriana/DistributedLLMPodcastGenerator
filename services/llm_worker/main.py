"""
Main entry point for LLM worker.

For RQ-based execution, use: python -m services.llm_worker.rq_worker
Or run: rq worker llm --path /path/to/project
"""

from worker import worker_loop

if __name__ == "__main__":
    # Legacy worker loop (polls database)
    # For new implementations, use RQ workers instead
    worker_loop()
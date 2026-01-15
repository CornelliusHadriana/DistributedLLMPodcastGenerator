from fastapi import FastAPI
from api.routes import ingest, status, episode

app = FastAPI(
    title="Newsletter to Podcast API",
    description="Service-based job queue architecture for converting newsletters to podcasts",
    version="1.0.0"
)

# Include routers
app.include_router(ingest.router, tags=["ingestion"])
app.include_router(status.router, tags=["status"])
app.include_router(episode.router, tags=["episodes"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Newsletter to Podcast API",
        "version": "1.0.0",
        "endpoints": {
            "POST /ingest": "Ingest an article and enqueue normalization job",
            "GET /status/{article_id}": "Get pipeline status for an article",
            "GET /episode/{article_id}": "Get final script and audio URL"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
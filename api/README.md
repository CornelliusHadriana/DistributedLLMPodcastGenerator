# FastAPI Application

Lightweight control plane API for the Newsletter → Podcast pipeline.

## Endpoints

### POST /ingest
Accepts article data and enqueues a normalization job.

**Request Body:**
```json
{
  "title": "Article Title (optional)",
  "url": "https://example.com/article (optional)",
  "raw_text": "Full article text...",
  "source": "Newsletter Name (optional)"
}
```

**Response:**
```json
{
  "article_id": "507f1f77bcf86cd799439011",
  "status": "ingested",
  "message": "Article ingested and normalization job enqueued"
}
```

**Behavior:**
- Stores raw article in MongoDB
- Sets initial pipeline status to "pending" for all stages
- Enqueues normalization job to `normalize` queue
- Returns immediately (no heavy processing)

### GET /status/{article_id}
Returns current pipeline status for an article.

**Response:**
```json
{
  "article_id": "507f1f77bcf86cd799439011",
  "overall_status": "in_progress",
  "stages": [
    {
      "stage": "normalize",
      "status": "completed",
      "updated_at": "2024-01-15T10:30:00"
    },
    {
      "stage": "summarize",
      "status": "running",
      "updated_at": "2024-01-15T10:35:00"
    },
    // ... other stages
  ],
  "created_at": "2024-01-15T10:25:00"
}
```

**Pipeline Stages:**
1. `normalize` - Clean HTML/markdown, split into chunks
2. `summarize` - Summarize each chunk
3. `assemble` - Combine summaries into script
4. `text_to_speech` - Convert script to audio
5. `publish` - Upload and publish episode

**Status Values:**
- `pending` - Not started
- `running` - In progress
- `completed` - Finished successfully
- `failed` - Error occurred

### GET /episode/{article_id}
Returns final script and audio URL.

**Response:**
```json
{
  "article_id": "507f1f77bcf86cd799439011",
  "script": "Welcome to today's episode...",
  "audio_url": "https://storage.example.com/episodes/episode_123.mp3",
  "status": "published",
  "published_at": "2024-01-15T11:00:00"
}
```

**Note:** Returns `null` for `script` and `audio_url` if not yet available.

## Running the API

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Design Principles

1. **Lightweight** - Endpoints only read/write to MongoDB and enqueue jobs
2. **No Heavy Processing** - All work delegated to background workers
3. **Fast Response** - Returns immediately after enqueuing jobs
4. **Status Tracking** - Pipeline progress tracked in MongoDB

## Database Schema

Articles are stored in the `articles` collection with this structure:

```python
{
    "_id": ObjectId(),
    "title": str,
    "url": str,
    "raw_text": str,
    "source": str,
    "status": "ingested" | "normalized" | ... | "published",
    "pipeline_status": {
        "normalize": "pending" | "running" | "completed" | "failed",
        "summarize": "...",
        "assemble": "...",
        "text_to_speech": "...",
        "publish": "..."
    },
    "script": str,  # Added by Assembly service
    "audio_url": str,  # Added by Publisher service
    "created_at": datetime,
    "updated_at": datetime,
    "published_at": datetime
}
```

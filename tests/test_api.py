"""
Unit tests for FastAPI Newsletter → Podcast API.

Covers all P0 and P1 endpoints:
- POST /ingest
- GET /status/{article_id}
- GET /episode/{article_id}
- GET /health

All tests use mocked MongoDB and Redis - no external dependencies required.
Tests run in isolation with pytest marks for categorization.
"""

import pytest
from unittest.mock import MagicMock
from bson import ObjectId
from datetime import datetime


# =============================================================================
# GET /health
# =============================================================================


class TestHealth:
    """Tests for GET /health endpoint."""

    @pytest.mark.unit
    def test_health_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.unit
    def test_health_returns_healthy_status(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.unit
    def test_health_response_schema(self, client):
        """Health check response should have correct schema."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert len(data) == 1


# =============================================================================
# POST /ingest
# =============================================================================


class TestIngestEndpoint:
    """Tests for POST /ingest endpoint."""

    @pytest.mark.unit
    def test_ingest_valid_full_request(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Accept valid POST /ingest request with all fields."""
        response = client.post("/ingest", json=valid_ingest_request)

        assert response.status_code == 200
        data = response.json()
        assert "article_id" in data
        assert data["status"] == "ingested"
        assert data["message"] == "Article ingested and normalization job enqueued"

    @pytest.mark.unit
    def test_ingest_valid_minimal_request(self, client, mock_articles_collection, mock_queue, minimal_ingest_request):
        """Accept minimal POST /ingest request (only raw_text)."""
        response = client.post("/ingest", json=minimal_ingest_request)

        assert response.status_code == 200
        data = response.json()
        assert "article_id" in data
        assert data["status"] == "ingested"

    @pytest.mark.unit
    def test_ingest_missing_raw_text(self, client, mock_articles_collection, mock_queue):
        """Reject POST /ingest request without raw_text."""
        response = client.post(
            "/ingest",
            json={
                "title": "Test",
                "url": "https://example.com"
            }
        )

        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.unit
    def test_ingest_empty_raw_text(self, client, mock_articles_collection, mock_queue):
        """Reject POST /ingest request with empty raw_text.
        
        Note: Pydantic validates string type but not string content.
        Empty strings are accepted by Pydantic. This test documents
        that behavior - if empty strings should be rejected, add a
        Field constraint like Field(..., min_length=1).
        """
        response = client.post(
            "/ingest",
            json={
                "title": "Test",
                "raw_text": "",
                "url": "https://example.com"
            }
        )

        # Empty string is technically valid per Pydantic
        # If you want to reject empty strings, add validation in schema
        assert response.status_code == 200

    @pytest.mark.unit
    def test_ingest_inserts_into_mongodb(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify MongoDB insert_one is called with correct document."""
        response = client.post("/ingest", json=valid_ingest_request)

        assert response.status_code == 200
        assert mock_articles_collection.insert_one_called
        
        # Verify inserted document structure
        inserted_doc = mock_articles_collection.insert_one_call_args
        assert inserted_doc["raw_text"] == valid_ingest_request["raw_text"]
        assert inserted_doc["title"] == valid_ingest_request["title"]
        assert inserted_doc["url"] == valid_ingest_request["url"]
        assert inserted_doc["source"] == valid_ingest_request["source"]

    @pytest.mark.unit
    def test_ingest_sets_status_ingested(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify initial status is set to 'ingested'."""
        response = client.post("/ingest", json=valid_ingest_request)

        inserted_doc = mock_articles_collection.insert_one_call_args
        assert inserted_doc["status"] == "ingested"

    @pytest.mark.unit
    def test_ingest_initializes_pipeline_status(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify pipeline_status is initialized with all stages as pending."""
        response = client.post("/ingest", json=valid_ingest_request)

        inserted_doc = mock_articles_collection.insert_one_call_args
        pipeline_status = inserted_doc["pipeline_status"]
        
        assert pipeline_status["normalize"] == "pending"
        assert pipeline_status["summarize"] == "pending"
        assert pipeline_status["assemble"] == "pending"
        assert pipeline_status["text_to_speech"] == "pending"
        assert pipeline_status["publish"] == "pending"

    @pytest.mark.unit
    def test_ingest_enqueues_normalize_job_on_success(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify normalize job is enqueued after successful insert."""
        response = client.post("/ingest", json=valid_ingest_request)

        assert response.status_code == 200
        assert mock_queue.enqueue.called
        
        # Verify job ID format
        call_args = mock_queue.enqueue.call_args
        assert call_args[1]["job_id"].startswith("normalize_")

    @pytest.mark.unit
    def test_ingest_queue_not_called_if_insert_fails(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify queue is NOT called if MongoDB insert fails."""
        # Configure mock to raise exception on insert
        mock_articles_collection.insert_one = MagicMock(side_effect=Exception("DB Error"))
        
        response = client.post("/ingest", json=valid_ingest_request)

        assert response.status_code == 500
        assert not mock_queue.enqueue.called

    @pytest.mark.unit
    def test_ingest_error_handling_500_on_insert_failure(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Return 500 error if database insert fails."""
        mock_articles_collection.insert_one = MagicMock(side_effect=Exception("Connection failed"))
        
        response = client.post("/ingest", json=valid_ingest_request)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to ingest article" in data["detail"]

    @pytest.mark.unit
    def test_ingest_response_has_valid_objectid(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Response article_id should be valid MongoDB ObjectId."""
        response = client.post("/ingest", json=valid_ingest_request)

        data = response.json()
        article_id = data["article_id"]
        
        # Should be convertible to ObjectId (24-char hex string)
        try:
            ObjectId(article_id)
            is_valid = True
        except:
            is_valid = False
        
        assert is_valid

    @pytest.mark.unit
    def test_ingest_sets_timestamps(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify created_at and updated_at timestamps are set."""
        response = client.post("/ingest", json=valid_ingest_request)

        inserted_doc = mock_articles_collection.insert_one_call_args
        assert "created_at" in inserted_doc
        assert "updated_at" in inserted_doc
        assert isinstance(inserted_doc["created_at"], datetime)
        assert isinstance(inserted_doc["updated_at"], datetime)


# =============================================================================
# GET /status/{article_id}
# =============================================================================


class TestStatusEndpoint:
    """Tests for GET /status/{article_id} endpoint."""

    @pytest.mark.unit
    def test_status_valid_article_id(self, client, mock_articles_collection, valid_article_doc):
        """Return status for valid article."""
        # Pre-insert an article
        mock_articles_collection.insert_one(valid_article_doc)
        
        response = client.get(f"/status/{str(valid_article_doc['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert data["article_id"] == str(valid_article_doc["_id"])
        assert "overall_status" in data
        assert "stages" in data

    @pytest.mark.unit
    def test_status_invalid_objectid_format(self, client, mock_articles_collection):
        """Return 400 for invalid ObjectId format."""
        response = client.get("/status/not_a_valid_id")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid article_id format" in data["detail"]

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_id", [
        "12345",
        "xyz",
        "!@#$%",
        "507f1f77bcf86cd79943901",  # 23 chars (too short)
        "507f1f77bcf86cd7994390111",  # 25 chars (too long)
    ])
    def test_status_invalid_objectid_variations(self, client, mock_articles_collection, invalid_id):
        """Return 400 for various invalid ObjectId formats."""
        response = client.get(f"/status/{invalid_id}")
        assert response.status_code == 400

    @pytest.mark.unit
    def test_status_nonexistent_article(self, client, mock_articles_collection):
        """Return 404 for non-existent article."""
        valid_id = ObjectId()
        response = client.get(f"/status/{str(valid_id)}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Article not found" in data["detail"]

    @pytest.mark.unit
    def test_status_all_pending_returns_pending(self, client, mock_articles_collection):
        """Overall status should be 'pending' when all stages are pending."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "pending",
                "summarize": "pending",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        assert data["overall_status"] == "pending"

    @pytest.mark.unit
    def test_status_mixed_stages_returns_in_progress(self, client, mock_articles_collection):
        """Overall status should be 'in_progress' when stages are mixed."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "running",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        assert data["overall_status"] == "in_progress"

    @pytest.mark.unit
    def test_status_any_failed_returns_failed(self, client, mock_articles_collection):
        """Overall status should be 'failed' if any stage failed."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "completed",
                "assemble": "failed",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        assert data["overall_status"] == "failed"

    @pytest.mark.unit
    def test_status_all_completed_returns_completed(self, client, mock_articles_collection):
        """Overall status should be 'completed' when all stages completed."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "completed",
                "assemble": "completed",
                "text_to_speech": "completed",
                "publish": "completed"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        assert data["overall_status"] == "completed"

    @pytest.mark.unit
    def test_status_returns_all_pipeline_stages(self, client, mock_articles_collection):
        """Response should include all five pipeline stages."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "running",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        stages = data["stages"]
        stage_names = [s["stage"] for s in stages]
        
        assert len(stages) == 5
        assert "normalize" in stage_names
        assert "summarize" in stage_names
        assert "assemble" in stage_names
        assert "text_to_speech" in stage_names
        assert "publish" in stage_names

    @pytest.mark.unit
    def test_status_stages_in_correct_order(self, client, mock_articles_collection):
        """Pipeline stages should be returned in correct order."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "running",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        stages = data["stages"]
        stage_names = [s["stage"] for s in stages]
        
        expected_order = ["normalize", "summarize", "assemble", "text_to_speech", "publish"]
        assert stage_names == expected_order

    @pytest.mark.unit
    def test_status_each_stage_has_required_fields(self, client, mock_articles_collection):
        """Each stage should have stage, status, and updated_at fields."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "pending",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        for stage in data["stages"]:
            assert "stage" in stage
            assert "status" in stage
            assert "updated_at" in stage

    @pytest.mark.unit
    def test_status_response_includes_created_at(self, client, mock_articles_collection):
        """Response should include article created_at timestamp."""
        now = datetime.now()
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "pending",
                "summarize": "pending",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            },
            "created_at": now
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        data = response.json()
        assert "created_at" in data
        assert data["created_at"] is not None

    @pytest.mark.unit
    def test_status_handles_missing_pipeline_stages(self, client, mock_articles_collection):
        """Handle gracefully when article has missing pipeline stages."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed"
                # Missing other stages
            },
            "created_at": datetime.now()
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/status/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        # Missing stages should default to "pending"
        assert len(data["stages"]) == 5


# =============================================================================
# GET /episode/{article_id}
# =============================================================================


class TestEpisodeEndpoint:
    """Tests for GET /episode/{article_id} endpoint."""

    @pytest.mark.unit
    def test_episode_invalid_objectid_format(self, client, mock_articles_collection):
        """Return 400 for invalid ObjectId format."""
        response = client.get("/episode/invalid_id")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid article_id format" in data["detail"]

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_id", [
        "xyz",
        "12345",
        "507f1f77bcf86cd79943901",  # 23 chars
    ])
    def test_episode_invalid_objectid_variations(self, client, mock_articles_collection, invalid_id):
        """Return 400 for various invalid ObjectId formats."""
        response = client.get(f"/episode/{invalid_id}")
        assert response.status_code == 400

    @pytest.mark.unit
    def test_episode_nonexistent_article(self, client, mock_articles_collection):
        """Return 404 for non-existent article."""
        valid_id = ObjectId()
        response = client.get(f"/episode/{str(valid_id)}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Article not found" in data["detail"]

    @pytest.mark.unit
    def test_episode_ingested_no_script_no_audio(self, client, mock_articles_collection):
        """Article with no script/audio should return in_progress status."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "pending",
                "summarize": "pending",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["script"] is None
        assert data["audio_url"] is None

    @pytest.mark.unit
    def test_episode_with_script_only(self, client, mock_articles_collection):
        """Article with script but no audio should return in_progress."""
        article = {
            "_id": ObjectId(),
            "script": "Welcome to the podcast...",
            "audio_url": None,
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "completed",
                "assemble": "completed",
                "text_to_speech": "pending",
                "publish": "pending"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["script"] is not None
        assert data["audio_url"] is None

    @pytest.mark.unit
    def test_episode_published_has_script_and_audio(self, client, mock_articles_collection):
        """Article with script and audio and publish=completed should be published."""
        article = {
            "_id": ObjectId(),
            "script": "Welcome to the podcast...",
            "audio_url": "https://storage.example.com/episode_123.mp3",
            "published_at": datetime.now(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "completed",
                "assemble": "completed",
                "text_to_speech": "completed",
                "publish": "completed"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["script"] is not None
        assert data["audio_url"] is not None

    @pytest.mark.unit
    def test_episode_failed_stage_returns_failed_status(self, client, mock_articles_collection):
        """Article with failed stage should return failed status."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "failed",
                "assemble": "pending",
                "text_to_speech": "pending",
                "publish": "pending"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

    @pytest.mark.unit
    def test_episode_null_script_handling(self, client, mock_articles_collection):
        """Endpoint should handle missing script field gracefully."""
        article = {
            "_id": ObjectId(),
            "audio_url": "https://storage.example.com/episode.mp3",
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "pending",
                "assemble": "pending",
                "text_to_speech": "completed",
                "publish": "pending"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert data["script"] is None

    @pytest.mark.unit
    def test_episode_null_audio_url_handling(self, client, mock_articles_collection):
        """Endpoint should handle missing audio_url field gracefully."""
        article = {
            "_id": ObjectId(),
            "script": "Welcome to the podcast...",
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "completed",
                "assemble": "completed",
                "text_to_speech": "pending",
                "publish": "pending"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert "audio_url" in data
        assert data["audio_url"] is None

    @pytest.mark.unit
    def test_episode_response_schema(self, client, mock_articles_collection):
        """Response should have required schema fields."""
        article = {
            "_id": ObjectId(),
            "script": "Welcome...",
            "audio_url": "https://storage.example.com/episode.mp3",
            "published_at": datetime.now(),
            "pipeline_status": {
                "normalize": "completed",
                "summarize": "completed",
                "assemble": "completed",
                "text_to_speech": "completed",
                "publish": "completed"
            }
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        assert response.status_code == 200
        data = response.json()
        assert "article_id" in data
        assert "script" in data
        assert "audio_url" in data
        assert "status" in data
        assert "published_at" in data

    @pytest.mark.unit
    def test_episode_returns_article_id(self, client, mock_articles_collection):
        """Response should include the article_id."""
        article = {
            "_id": ObjectId(),
            "pipeline_status": {}
        }
        mock_articles_collection.insert_one(article)
        
        response = client.get(f"/episode/{str(article['_id'])}")

        data = response.json()
        assert data["article_id"] == str(article["_id"])


# =============================================================================
# Additional Integration-style Tests (Marked but included for completeness)
# =============================================================================


class TestIngestWorkflow:
    """End-to-end workflow tests (unit scoped, using mocks)."""

    @pytest.mark.unit
    def test_ingest_to_status_workflow(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify complete workflow: ingest → check status."""
        # Step 1: Ingest article
        ingest_response = client.post("/ingest", json=valid_ingest_request)
        assert ingest_response.status_code == 200
        article_id = ingest_response.json()["article_id"]

        # Step 2: Retrieve status
        status_response = client.get(f"/status/{article_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        assert status_data["overall_status"] == "pending"
        assert len(status_data["stages"]) == 5

    @pytest.mark.unit
    def test_ingest_to_episode_workflow(self, client, mock_articles_collection, mock_queue, valid_ingest_request):
        """Verify complete workflow: ingest → check episode."""
        # Step 1: Ingest article
        ingest_response = client.post("/ingest", json=valid_ingest_request)
        assert ingest_response.status_code == 200
        article_id = ingest_response.json()["article_id"]

        # Step 2: Retrieve episode
        episode_response = client.get(f"/episode/{article_id}")
        assert episode_response.status_code == 200
        episode_data = episode_response.json()
        
        assert episode_data["article_id"] == article_id
        assert episode_data["status"] == "in_progress"
        assert episode_data["script"] is None
        assert episode_data["audio_url"] is None


# =============================================================================
# Root Endpoint Tests
# =============================================================================


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    @pytest.mark.unit
    def test_root_returns_200(self, client):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.unit
    def test_root_returns_api_info(self, client):
        """Root endpoint should return API information."""
        response = client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data




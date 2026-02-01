"""
Shared pytest fixtures for API tests.

Provides:
- TestClient for FastAPI app
- Mocked MongoDB (db.articles collection)
- Mocked Redis queue (normalize_queue.enqueue)
- Mock object IDs for testing

All fixtures are unit-test scoped and isolated per test.
"""

import pytest
from unittest.mock import MagicMock, Mock
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime


@pytest.fixture
def client():
    """
    FastAPI TestClient for making requests.
    
    Must be imported after mocks are in place to use mocked dependencies.
    """
    from api.main import app
    return TestClient(app)


@pytest.fixture
def mock_mongo_db(monkeypatch):
    """
    Mock MongoDB articles collection.
    
    Returns a MagicMock collection that tracks calls and can be configured
    per test. Isolated per test.
    """
    mock_collection = MagicMock()
    
    # Mock the db module at the point where it's used
    monkeypatch.setattr("db.database.db", {})
    
    # Return the mock so tests can configure behavior
    return mock_collection


@pytest.fixture
def mock_queue(monkeypatch):
    """
    Mock Redis normalize_queue.
    
    Tracks enqueue calls without actually contacting Redis.
    Isolated per test.
    """
    mock_q = MagicMock()
    mock_q.enqueue = MagicMock(return_value=None)
    
    # Patch at the point where it's used (in ingest.py)
    monkeypatch.setattr(
        "api.routes.ingest.normalize_queue",
        mock_q
    )
    
    return mock_q


@pytest.fixture
def mock_articles_collection(monkeypatch):
    """
    Complete mock for db.articles collection with insert_one and find_one.
    
    Provides realistic MongoDB behavior for testing CRUD operations.
    """
    class MockArticlesCollection:
        def __init__(self):
            self.inserted_docs = {}  # Store inserted docs by _id
            self.insert_one_called = False
            self.insert_one_call_args = None
            
        def insert_one(self, doc):
            """Mock insert_one - assigns _id if not present."""
            self.insert_one_called = True
            self.insert_one_call_args = doc
            
            # Generate ObjectId if not present
            if "_id" not in doc:
                doc["_id"] = ObjectId()
            
            # Store the document
            self.inserted_docs[doc["_id"]] = doc
            
            # Return mock result with inserted_id
            result = MagicMock()
            result.inserted_id = doc["_id"]
            return result
        
        def find_one(self, query):
            """Mock find_one - retrieves by _id."""
            if "_id" in query:
                return self.inserted_docs.get(query["_id"])
            return None
        
        def find(self, query):
            """Mock find - returns cursor-like object."""
            results = [
                doc for doc in self.inserted_docs.values()
                if all(doc.get(k) == v for k, v in query.items())
            ]
            cursor = MagicMock()
            cursor.__iter__ = lambda: iter(results)
            return cursor
        
        def update_one(self, query, update):
            """Mock update_one."""
            if "_id" in query and query["_id"] in self.inserted_docs:
                doc = self.inserted_docs[query["_id"]]
                if "$set" in update:
                    doc.update(update["$set"])
                result = MagicMock()
                result.matched_count = 1
                return result
            result = MagicMock()
            result.matched_count = 0
            return result
    
    collection = MockArticlesCollection()
    
    # Create mock db object
    mock_db = MagicMock()
    mock_db.articles = collection
    
    # Patch db module at import points
    monkeypatch.setattr("db.db", mock_db)
    monkeypatch.setattr("api.routes.ingest.db", mock_db)
    monkeypatch.setattr("api.routes.status.db", mock_db)
    monkeypatch.setattr("api.routes.episode.db", mock_db)
    
    return collection


@pytest.fixture
def valid_article_doc():
    """Valid article document for testing."""
    article_id = ObjectId()
    return {
        "_id": article_id,
        "title": "Test Article",
        "url": "https://example.com/test",
        "raw_text": "This is test article content.",
        "source": "test_newsletter",
        "status": "ingested",
        "pipeline_status": {
            "normalize": "pending",
            "summarize": "pending",
            "assemble": "pending",
            "text_to_speech": "pending",
            "publish": "pending"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@pytest.fixture
def valid_ingest_request():
    """Valid POST /ingest request body."""
    return {
        "title": "Test Article",
        "url": "https://example.com/test",
        "raw_text": "This is test article content with sufficient length.",
        "source": "test_newsletter"
    }


@pytest.fixture
def minimal_ingest_request():
    """Minimal POST /ingest request (only required fields)."""
    return {
        "raw_text": "Minimal article content."
    }

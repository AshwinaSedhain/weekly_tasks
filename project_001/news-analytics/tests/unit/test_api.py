# This file is testing the FastAPI endpoints using the TestClient. It is mocking
# the database calls so the tests run without a real PostgreSQL or MongoDB instance.
# Every endpoint is tested for correct status codes and response structure.

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


def make_sample_article(article_id: str = "abc123") -> dict:
    # Returning a sample article dictionary that matches the shape stored in PostgreSQL.
    return {
        "id": article_id,
        "title": "Sample Article Title",
        "description": "Sample description",
        "content": "Sample content",
        "url": "https://example.com/article",
        "author": "Test Author",
        "source_name": "Test Source",
        "published_at": "2024-01-01T12:00:00",
        "collected_at": "2024-01-01T12:05:00",
        "source": "newsapi_headlines",
        "category": "technology",
        "sentiment_label": "positive",
        "sentiment_score": 0.75,
        "keywords": ["python", "machine", "learning"],
        "cluster": 2,
        "score": 0,
        "comments": 0,
    }


@pytest.fixture
def client():
    # Creating a TestClient for the FastAPI app with the database initialization
    # calls patched out so no real connections are needed during testing.
    with patch("api.database.postgres.init_schema"), \
         patch("api.database.mongo.init_indexes"):
        from api.main import app
        return TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        # Verifying that the health endpoint returns a 200 status code.
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        # Checking that the health response body contains status ok.
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"


class TestNewsEndpoints:

    @patch("api.routers.news.fetch_latest")
    def test_latest_news_returns_200(self, mock_fetch, client):
        # Verifying that /news/latest returns 200 when the database call succeeds.
        mock_fetch.return_value = [make_sample_article()]
        response = client.get("/news/latest")
        assert response.status_code == 200

    @patch("api.routers.news.fetch_latest")
    def test_latest_news_returns_articles_list(self, mock_fetch, client):
        # Checking that the response body contains an articles key with a list value.
        mock_fetch.return_value = [make_sample_article("1"), make_sample_article("2")]
        response = client.get("/news/latest")
        data = response.json()
        assert "articles" in data
        assert len(data["articles"]) == 2

    @patch("api.routers.news.fetch_latest")
    def test_latest_news_pagination_params(self, mock_fetch, client):
        # Verifying that limit and offset query parameters are accepted without error.
        mock_fetch.return_value = []
        response = client.get("/news/latest?limit=10&offset=20")
        assert response.status_code == 200

    @patch("api.routers.news.search_articles")
    def test_search_returns_200(self, mock_search, client):
        # Verifying that /news/search returns 200 when a query parameter is provided.
        mock_search.return_value = [make_sample_article()]
        response = client.get("/news/search?q=python")
        assert response.status_code == 200

    @patch("api.routers.news.search_articles")
    def test_search_returns_query_in_response(self, mock_search, client):
        # Checking that the search response echoes back the query string submitted.
        mock_search.return_value = []
        response = client.get("/news/search?q=machine+learning")
        data = response.json()
        assert data["query"] == "machine learning"

    def test_search_without_query_returns_422(self, client):
        # Verifying that /news/search returns 422 when the required q parameter is missing.
        response = client.get("/news/search")
        assert response.status_code == 422


class TestAnalyticsEndpoints:

    @patch("api.routers.analytics.fetch_sentiment_summary")
    def test_sentiment_returns_200(self, mock_sentiment, client):
        # Verifying that /analytics/sentiment returns 200.
        mock_sentiment.return_value = {"positive": 10, "negative": 5, "neutral": 15}
        response = client.get("/analytics/sentiment")
        assert response.status_code == 200

    @patch("api.routers.analytics.fetch_sentiment_summary")
    def test_sentiment_response_contains_sentiment_key(self, mock_sentiment, client):
        # Checking that the sentiment response body contains a sentiment key.
        mock_sentiment.return_value = {"positive": 10, "negative": 5, "neutral": 15}
        response = client.get("/analytics/sentiment")
        data = response.json()
        assert "sentiment" in data

    @patch("api.routers.analytics.count_by_source")
    def test_sources_returns_200(self, mock_sources, client):
        # Verifying that /analytics/sources returns 200.
        mock_sources.return_value = {"newsapi_headlines": 50, "hackernews": 30}
        response = client.get("/analytics/sources")
        assert response.status_code == 200


class TestScrapeEndpoint:

    def test_scrape_run_returns_200(self, client):
        # Verifying that POST /scrape/run returns 200 without blocking.
        response = client.post("/scrape/run")
        assert response.status_code == 200

    def test_scrape_run_returns_ok_status(self, client):
        # Checking that the scrape response body contains status ok.
        response = client.post("/scrape/run")
        data = response.json()
        assert data["status"] == "ok"

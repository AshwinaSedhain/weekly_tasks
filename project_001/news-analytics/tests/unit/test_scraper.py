# This file is testing the scraper components. It is verifying that the NewsAPI
# client normalizes articles correctly, that the Hacker News scraper produces the
# expected schema, and that the deduplicator correctly filters out articles it has
# already seen in previous batches.

import hashlib
from unittest.mock import patch

import pytest

from scraper.newsapi_client import NewsAPIClient
from scraper.hackernews_scraper import HackerNewsScraper
from scraper.deduplicator import Deduplicator


def make_raw_newsapi_article(url: str = "https://example.com/article") -> dict:
    # Returning a minimal raw NewsAPI article dictionary that matches the shape
    # returned by the real API.
    return {
        "title": "Test Article Title",
        "description": "Test description",
        "content": "Test content",
        "url": url,
        "author": "Test Author",
        "source": {"name": "Test Source"},
        "publishedAt": "2024-01-01T12:00:00Z",
    }


def make_raw_hn_story(story_id: int = 1, url: str = "https://example.com/hn") -> dict:
    # Returning a minimal raw Hacker News story dictionary that matches the shape
    # returned by the Firebase API.
    return {
        "id": story_id,
        "title": "HN Story Title",
        "text": "HN story text",
        "url": url,
        "by": "hn_user",
        "time": 1704067200,
        "score": 100,
        "descendants": 50,
    }


class TestNewsAPIClient:

    def setup_method(self):
        self.client = NewsAPIClient(api_key="test_key")

    def test_normalize_produces_required_fields(self):
        # Checking that normalize returns a dictionary containing all required
        # fields with the correct types.
        raw = make_raw_newsapi_article()
        result = self.client._normalize(raw, source="newsapi_headlines")
        required_fields = [
            "id", "title", "description", "content", "url",
            "author", "source_name", "published_at", "collected_at",
            "source", "category",
        ]
        for field in required_fields:
            assert field in result, f"Field '{field}' missing from normalized article"

    def test_normalize_generates_deterministic_id(self):
        # Verifying that normalizing the same article twice produces the same ID.
        raw = make_raw_newsapi_article(url="https://example.com/stable")
        result1 = self.client._normalize(raw, source="newsapi_headlines")
        result2 = self.client._normalize(raw, source="newsapi_headlines")
        assert result1["id"] == result2["id"]

    def test_normalize_id_is_md5_of_url(self):
        # Confirming that the article ID is the MD5 hash of the article URL.
        url = "https://example.com/article"
        raw = make_raw_newsapi_article(url=url)
        result = self.client._normalize(raw, source="newsapi_headlines")
        expected_id = hashlib.md5(url.encode()).hexdigest()
        assert result["id"] == expected_id

    def test_normalize_sets_source_field(self):
        # Checking that the source field matches the source argument passed to normalize.
        raw = make_raw_newsapi_article()
        result = self.client._normalize(raw, source="newsapi_everything")
        assert result["source"] == "newsapi_everything"

    @patch("scraper.newsapi_client.requests.Session.get")
    def test_fetch_top_headlines_returns_empty_on_error(self, mock_get):
        # Verifying that fetch_top_headlines returns an empty list when the HTTP
        # request raises an exception instead of crashing.
        mock_get.side_effect = Exception("Network error")
        result = self.client.fetch_top_headlines()
        assert result == []


class TestHackerNewsScraper:

    def setup_method(self):
        self.scraper = HackerNewsScraper(max_stories=10)

    def test_normalize_produces_required_fields(self):
        # Checking that normalize returns all required fields for a Hacker News story.
        raw = make_raw_hn_story()
        result = self.scraper._normalize(raw)
        required_fields = [
            "id", "title", "url", "author", "source_name",
            "published_at", "collected_at", "source", "category",
            "score", "comments",
        ]
        for field in required_fields:
            assert field in result, f"Field '{field}' missing from normalized story"

    def test_normalize_source_is_hackernews(self):
        # Verifying that the source field is always set to hackernews.
        raw = make_raw_hn_story()
        result = self.scraper._normalize(raw)
        assert result["source"] == "hackernews"

    def test_normalize_score_is_preserved(self):
        # Checking that the score field from the raw story is preserved.
        raw = make_raw_hn_story()
        raw["score"] = 250
        result = self.scraper._normalize(raw)
        assert result["score"] == 250


class TestDeduplicator:

    def setup_method(self):
        self.dedup = Deduplicator()

    def _make_article(self, article_id: str) -> dict:
        return {"id": article_id, "title": f"Article {article_id}"}

    def test_first_batch_passes_through_completely(self):
        # Verifying that all articles in the first batch are returned because
        # none have been seen before.
        articles = [self._make_article(str(i)) for i in range(5)]
        result = self.dedup.filter_new(articles)
        assert len(result) == 5

    def test_duplicate_articles_are_filtered(self):
        # Checking that articles submitted in a second batch with the same IDs
        # as the first batch are filtered out completely.
        articles = [self._make_article(str(i)) for i in range(5)]
        self.dedup.filter_new(articles)
        result = self.dedup.filter_new(articles)
        assert len(result) == 0

    def test_partial_duplicates_are_handled(self):
        # Verifying that when a batch contains a mix of new and already-seen
        # articles, only the new ones are returned.
        first_batch = [self._make_article(str(i)) for i in range(3)]
        second_batch = [self._make_article(str(i)) for i in range(2, 5)]
        self.dedup.filter_new(first_batch)
        result = self.dedup.filter_new(second_batch)
        assert len(result) == 2
        returned_ids = {a["id"] for a in result}
        assert returned_ids == {"3", "4"}

    def test_articles_without_id_are_filtered(self):
        # Checking that articles missing an id field are excluded from the output.
        articles = [{"title": "No ID article"}]
        result = self.dedup.filter_new(articles)
        assert len(result) == 0

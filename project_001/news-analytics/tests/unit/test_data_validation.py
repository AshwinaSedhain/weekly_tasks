# This file is testing data validation across the pipeline. It is verifying that
# the normalized article schema is consistent between the two data sources and that
# all required fields are present with the correct types. This ensures the pipeline
# never receives unexpected data shapes that could cause silent failures downstream.

import pytest
from scraper.newsapi_client import NewsAPIClient
from scraper.hackernews_scraper import HackerNewsScraper

REQUIRED_FIELDS = [
    "id", "title", "description", "content", "url",
    "author", "source_name", "published_at", "collected_at",
    "source", "category",
]

STRING_FIELDS = [
    "id", "title", "description", "content", "url",
    "author", "source_name", "published_at", "collected_at",
    "source", "category",
]


def make_newsapi_article() -> dict:
    client = NewsAPIClient(api_key="test")
    return client._normalize(
        {
            "title": "Test Title",
            "description": "Test description",
            "content": "Test content",
            "url": "https://example.com/test",
            "author": "Author",
            "source": {"name": "Source"},
            "publishedAt": "2024-01-01T00:00:00Z",
        },
        source="newsapi_headlines",
    )


def make_hn_article() -> dict:
    scraper = HackerNewsScraper()
    return scraper._normalize(
        {
            "id": 12345,
            "title": "HN Title",
            "text": "HN text",
            "url": "https://example.com/hn",
            "by": "user123",
            "time": 1704067200,
            "score": 100,
            "descendants": 50,
        }
    )


class TestArticleSchema:

    @pytest.mark.parametrize("article_factory", [make_newsapi_article, make_hn_article])
    def test_all_required_fields_present(self, article_factory):
        # Verifying that every required field is present in the normalized article
        # for both data sources.
        article = article_factory()
        for field in REQUIRED_FIELDS:
            assert field in article, f"Required field '{field}' missing"

    @pytest.mark.parametrize("article_factory", [make_newsapi_article, make_hn_article])
    def test_string_fields_are_strings(self, article_factory):
        # Verifying that all string fields contain string values and not None.
        article = article_factory()
        for field in STRING_FIELDS:
            value = article.get(field)
            assert isinstance(value, str), (
                f"Field '{field}' should be str but got {type(value)}"
            )

    @pytest.mark.parametrize("article_factory", [make_newsapi_article, make_hn_article])
    def test_id_is_non_empty(self, article_factory):
        # Verifying that the article ID is a non-empty string so it can be used
        # as a database primary key.
        article = article_factory()
        assert len(article["id"]) > 0

    @pytest.mark.parametrize("article_factory", [make_newsapi_article, make_hn_article])
    def test_url_starts_with_http(self, article_factory):
        # Verifying that the URL field starts with http so it is a valid web address.
        article = article_factory()
        assert article["url"].startswith("http")

    @pytest.mark.parametrize("article_factory", [make_newsapi_article, make_hn_article])
    def test_category_is_technology(self, article_factory):
        # Verifying that the category field is set to technology for all articles.
        article = article_factory()
        assert article["category"] == "technology"

    def test_newsapi_source_field_value(self):
        # Checking that the source field for a NewsAPI article is newsapi_headlines.
        article = make_newsapi_article()
        assert article["source"] == "newsapi_headlines"

    def test_hackernews_source_field_value(self):
        # Checking that the source field for a Hacker News article is hackernews.
        article = make_hn_article()
        assert article["source"] == "hackernews"

    def test_hackernews_has_score_field(self):
        # Verifying that Hacker News articles include a score field that is an integer.
        article = make_hn_article()
        assert "score" in article
        assert isinstance(article["score"], int)

    def test_hackernews_has_comments_field(self):
        # Verifying that Hacker News articles include a comments field that is an integer.
        article = make_hn_article()
        assert "comments" in article
        assert isinstance(article["comments"], int)

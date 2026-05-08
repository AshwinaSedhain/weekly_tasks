# This file is testing the full data pipeline integration. It is verifying that
# articles flow correctly from the collector through the ML pipeline and into the
# database layer. These tests require a running PostgreSQL and MongoDB instance
# which are provided by the CI/CD service containers defined in the workflow file.

import os
import pytest

POSTGRES_AVAILABLE = all([
    os.getenv("POSTGRES_HOST"),
    os.getenv("POSTGRES_USER"),
    os.getenv("POSTGRES_PASSWORD"),
])

MONGO_AVAILABLE = bool(os.getenv("MONGO_URI"))


def make_test_article(article_id: str = "test_001") -> dict:
    # Returning a fully populated article dictionary that can be inserted into
    # both PostgreSQL and MongoDB for integration testing.
    return {
        "id": article_id,
        "title": "Integration Test Article",
        "description": "Testing the full pipeline integration",
        "content": "Full content of the integration test article",
        "url": f"https://example.com/{article_id}",
        "author": "Test Author",
        "source_name": "Test Source",
        "published_at": "2024-01-01T12:00:00",
        "collected_at": "2024-01-01T12:05:00",
        "source": "test",
        "category": "technology",
        "sentiment": {"label": "neutral", "compound": 0.0},
        "keywords": ["integration", "test", "pipeline"],
        "cluster": 0,
        "score": 0,
        "comments": 0,
    }


@pytest.mark.skipif(not POSTGRES_AVAILABLE, reason="PostgreSQL not available")
class TestPostgresIntegration:

    def setup_method(self):
        from api.database.postgres import init_schema
        init_schema()

    def test_insert_and_fetch_article(self):
        # Inserting a test article into PostgreSQL and fetching it back to verify
        # the round-trip works correctly.
        from api.database.postgres import insert_article, fetch_latest
        article = make_test_article("pg_test_001")
        insert_article(article)
        results = fetch_latest(limit=10)
        ids = [r["id"] for r in results]
        assert "pg_test_001" in ids

    def test_duplicate_insert_does_not_raise(self):
        # Verifying that inserting the same article twice does not raise an exception
        # due to the ON CONFLICT DO NOTHING clause.
        from api.database.postgres import insert_article
        article = make_test_article("pg_test_dup")
        insert_article(article)
        insert_article(article)

    def test_search_finds_inserted_article(self):
        # Inserting an article with a unique title and searching for it to verify
        # the search function works correctly.
        from api.database.postgres import insert_article, search_articles
        article = make_test_article("pg_test_search")
        article["title"] = "UniqueSearchableTitle12345"
        insert_article(article)
        results = search_articles("UniqueSearchableTitle12345")
        assert len(results) >= 1
        assert results[0]["title"] == "UniqueSearchableTitle12345"


@pytest.mark.skipif(not MONGO_AVAILABLE, reason="MongoDB not available")
class TestMongoIntegration:

    def setup_method(self):
        from api.database.mongo import init_indexes
        init_indexes()

    def test_insert_and_fetch_raw_article(self):
        # Inserting a raw article into MongoDB and fetching it back to verify
        # the round-trip works correctly.
        from api.database.mongo import insert_raw_article, fetch_raw_articles
        article = make_test_article("mongo_test_001")
        insert_raw_article(article)
        results = fetch_raw_articles(limit=50)
        ids = [r["id"] for r in results]
        assert "mongo_test_001" in ids

    def test_upsert_does_not_create_duplicate(self):
        # Verifying that inserting the same article twice results in only one
        # document in the collection.
        from api.database.mongo import insert_raw_article, get_collection
        article = make_test_article("mongo_test_upsert")
        insert_raw_article(article)
        insert_raw_article(article)
        col = get_collection("raw_articles")
        count = col.count_documents({"id": "mongo_test_upsert"})
        assert count == 1


class TestMLPipelineIntegration:

    def test_full_pipeline_processes_batch(self):
        # Running a batch of 10 articles through the full ML pipeline and verifying
        # that every article is enriched with sentiment and keywords.
        from ml.pipeline import MLPipeline
        pipeline = MLPipeline()
        articles = [make_test_article(str(i)) for i in range(10)]
        for i, article in enumerate(articles):
            article["title"] = f"Technology article about machine learning number {i}"
            article["description"] = f"Deep learning and AI research article {i}"
        result = pipeline.process(articles)
        assert len(result) == 10
        for article in result:
            assert "sentiment" in article
            assert "keywords" in article
            assert article["sentiment"]["label"] in ["positive", "negative", "neutral"]

    def test_pipeline_handles_none_fields(self):
        # Verifying that the pipeline handles articles with None fields without
        # crashing and still returns enriched results.
        from ml.pipeline import MLPipeline
        pipeline = MLPipeline()
        articles = [{"id": "1", "title": None, "description": None,
                     "content": None, "source": "test", "category": "technology"}]
        result = pipeline.process(articles)
        assert len(result) == 1
        assert "sentiment" in result[0]

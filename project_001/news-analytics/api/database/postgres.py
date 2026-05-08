# This file is managing the PostgreSQL connection and providing helper functions
# for inserting and querying articles. PostgreSQL is storing the structured analytics
# data including sentiment scores, keywords, and cluster labels that the FastAPI
# endpoints serve to clients and the dashboard displays.

import logging
import os
from typing import Optional

import psycopg2
import psycopg2.extras
import psycopg2.extensions
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "newsdb")
DB_USER = os.getenv("POSTGRES_USER", "newsuser")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "newspass")

_pool: Optional[ThreadedConnectionPool] = None


def get_pool() -> ThreadedConnectionPool:
    # Creating the connection pool on first call and returning it on subsequent
    # calls. Using a pool avoids opening a new TCP connection for every database
    # operation which would be very slow.
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        logger.info("PostgreSQL connection pool created")
    return _pool


def init_schema() -> None:
    # Creating the articles table if it does not already exist. Safe to call on
    # every application startup because the CREATE TABLE statement uses IF NOT EXISTS.
    # Also creating indexes on published_at and source for faster queries.
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id              TEXT PRIMARY KEY,
                    title           TEXT,
                    description     TEXT,
                    content         TEXT,
                    url             TEXT,
                    author          TEXT,
                    source_name     TEXT,
                    published_at    TEXT,
                    collected_at    TEXT,
                    processed_at    TEXT,
                    source          TEXT,
                    category        TEXT,
                    sentiment_label TEXT,
                    sentiment_score FLOAT,
                    keywords        TEXT[],
                    cluster         INTEGER,
                    score           INTEGER DEFAULT 0,
                    comments        INTEGER DEFAULT 0
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_published_at
                ON articles (published_at DESC);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_source
                ON articles (source);
            """)
        conn.commit()
        logger.info("PostgreSQL schema initialized")
    finally:
        pool.putconn(conn)


def _safe_str(value) -> str:
    # Converting any value to a string safely. Returning an empty string for
    # None values so no database constraint is violated.
    if value is None:
        return ""
    return str(value)


def _safe_keywords(value) -> list:
    # Ensuring the keywords field is always a plain Python list of strings.
    # psycopg2 adapts a Python list to a PostgreSQL TEXT array automatically
    # when all items are strings.
    if not value:
        return []
    if isinstance(value, list):
        return [str(k) for k in value]
    return []


def insert_article(article: dict) -> None:
    # Inserting a single enriched article into the articles table. Using ON CONFLICT
    # DO NOTHING so inserting the same article ID twice is a no-op rather than an
    # error. Handling both nested dict sentiment and flat sentiment fields that may
    # come from different parts of the pipeline.
    pool = get_pool()
    conn = pool.getconn()

    sentiment = article.get("sentiment")
    if isinstance(sentiment, dict):
        sentiment_label = sentiment.get("label", "neutral")
        sentiment_score = sentiment.get("compound", 0.0)
    else:
        sentiment_label = article.get("sentiment_label", "neutral")
        sentiment_score = article.get("sentiment_score", 0.0)

    keywords = _safe_keywords(article.get("keywords", []))

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO articles (
                    id, title, description, content, url, author,
                    source_name, published_at, collected_at, source,
                    category, sentiment_label, sentiment_score,
                    keywords, cluster, score, comments
                ) VALUES (
                    %(id)s, %(title)s, %(description)s, %(content)s,
                    %(url)s, %(author)s, %(source_name)s,
                    %(published_at)s, %(collected_at)s, %(source)s,
                    %(category)s, %(sentiment_label)s, %(sentiment_score)s,
                    %(keywords)s, %(cluster)s, %(score)s, %(comments)s
                )
                ON CONFLICT (id) DO NOTHING;
            """, {
                "id": _safe_str(article.get("id")),
                "title": _safe_str(article.get("title")),
                "description": _safe_str(article.get("description")),
                "content": _safe_str(article.get("content")),
                "url": _safe_str(article.get("url")),
                "author": _safe_str(article.get("author")),
                "source_name": _safe_str(article.get("source_name")),
                "published_at": _safe_str(article.get("published_at")),
                "collected_at": _safe_str(article.get("collected_at")),
                "source": _safe_str(article.get("source")),
                "category": _safe_str(article.get("category")),
                "sentiment_label": sentiment_label,
                "sentiment_score": float(sentiment_score) if sentiment_score else 0.0,
                "keywords": keywords,
                "cluster": article.get("cluster"),
                "score": int(article.get("score") or 0),
                "comments": int(article.get("comments") or 0),
            })
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Inserting article %s failing: %s", article.get("id"), exc)
        raise
    finally:
        pool.putconn(conn)


def insert_articles_batch(articles: list[dict]) -> int:
    # Inserting a batch of articles one by one and returning the number successfully
    # inserted. Skipping individual failures so one bad article does not block the rest.
    if not articles:
        return 0

    inserted = 0
    for article in articles:
        try:
            insert_article(article)
            inserted += 1
        except Exception as exc:
            logger.error("Batch insert skipping article %s: %s", article.get("id"), exc)

    logger.info("Batch inserted %d/%d articles into PostgreSQL", inserted, len(articles))
    return inserted


def fetch_latest(limit: int = 50, offset: int = 0) -> list[dict]:
    # Fetching the most recently collected articles from PostgreSQL ordered by
    # collected_at descending so the newest articles from all sources appear at
    # the top regardless of their original publication date.
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM articles ORDER BY collected_at DESC LIMIT %s OFFSET %s;",
                (limit, offset),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        pool.putconn(conn)


def search_articles(query: str, limit: int = 50) -> list[dict]:
    # Performing a case-insensitive full-text search on the title and description
    # columns using PostgreSQL ILIKE. Returning articles ordered by most recent first.
    pool = get_pool()
    conn = pool.getconn()
    pattern = f"%{query}%"
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM articles
                WHERE title ILIKE %s OR description ILIKE %s
                ORDER BY published_at DESC
                LIMIT %s;
                """,
                (pattern, pattern, limit),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        pool.putconn(conn)


def fetch_sentiment_summary() -> dict:
    # Counting articles by sentiment label and returning the totals as a dictionary
    # so the dashboard can render a pie chart showing the proportion of positive,
    # negative, and neutral news.
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT sentiment_label, COUNT(*) AS count
                FROM articles
                WHERE sentiment_label IS NOT NULL
                GROUP BY sentiment_label;
            """)
            return {row["sentiment_label"]: row["count"] for row in cur.fetchall()}
    finally:
        pool.putconn(conn)

# This file is defining the /analytics endpoints. It is providing routes for
# sentiment summaries, trending keywords, and source distribution data that the
# dashboard consumes to render its charts. All data comes from PostgreSQL and
# MongoDB so results are always available even after a server restart.

import logging

from fastapi import APIRouter, HTTPException

from api.database.postgres import fetch_sentiment_summary
from api.database.mongo import count_by_source

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/sentiment")
async def get_sentiment_summary() -> dict:
    # Returning the count of articles grouped by sentiment label from PostgreSQL.
    # The dashboard uses this to render the pie chart showing positive, negative,
    # and neutral proportions.
    try:
        summary = fetch_sentiment_summary()
        return {"status": "ok", "sentiment": summary}
    except Exception as exc:
        logger.error("Fetching sentiment summary failing: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch sentiment data")


@router.get("/trends")
async def get_trends(top_n: int = 20) -> dict:
    # Returning the top keywords by frequency from PostgreSQL. Unnesting the
    # keywords array column and counting how often each keyword appears across
    # all articles. This always returns data even after a restart because it
    # reads from the database rather than an in-memory counter.
    try:
        from api.database.postgres import get_pool
        import psycopg2.extras

        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT keyword, COUNT(*) AS current_count
                    FROM (
                        SELECT unnest(keywords) AS keyword
                        FROM articles
                        WHERE keywords IS NOT NULL
                          AND array_length(keywords, 1) > 0
                    ) AS kw
                    WHERE keyword != ''
                      AND length(keyword) > 2
                    GROUP BY keyword
                    ORDER BY current_count DESC
                    LIMIT %s;
                """, (top_n,))
                rows = cur.fetchall()
                trending = [
                    {
                        "keyword": row["keyword"],
                        "current_count": int(row["current_count"]),
                        "previous_count": 0,
                        "trend_score": int(row["current_count"]),
                    }
                    for row in rows
                ]
        finally:
            pool.putconn(conn)

        return {"status": "ok", "trending": trending}
    except Exception as exc:
        logger.error("Fetching trends failing: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(exc)}")


@router.get("/sources")
async def get_source_distribution() -> dict:
    # Returning the count of raw articles grouped by source from MongoDB.
    # Shows how many articles came from newsapi_headlines, newsapi_everything,
    # and hackernews.
    try:
        distribution = count_by_source()
        return {"status": "ok", "sources": distribution}
    except Exception as exc:
        logger.error("Fetching source distribution failing: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch source data")

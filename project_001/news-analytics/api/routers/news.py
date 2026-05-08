# This file is defining the /news endpoints. It is providing routes for fetching
# the latest articles and searching articles by keyword. Both endpoints support
# pagination through limit and offset query parameters so clients can load data
# in pages rather than all at once.

import logging

from fastapi import APIRouter, HTTPException, Query

from api.database.postgres import fetch_latest, search_articles

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/latest")
async def get_latest_news(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    # Returning the most recently collected articles from PostgreSQL. The limit
    # parameter controls how many articles are returned per page and offset
    # controls the starting position for pagination.
    try:
        articles = fetch_latest(limit=limit, offset=offset)
        return {
            "status": "ok",
            "count": len(articles),
            "offset": offset,
            "articles": articles,
        }
    except Exception as exc:
        logger.error("Fetching latest news failing: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch latest news")


@router.get("/search")
async def search_news(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    # Searching articles by keyword using a case-insensitive match on the title
    # and description columns. The q parameter is required and must be at least
    # one character long.
    try:
        articles = search_articles(query=q, limit=limit)
        return {
            "status": "ok",
            "query": q,
            "count": len(articles),
            "articles": articles,
        }
    except Exception as exc:
        logger.error("Searching articles failing: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to search articles")

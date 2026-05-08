# This file is defining the /metrics/live endpoint. It is returning live system
# health and statistics that the dashboard polls to show the current state of the
# pipeline including total article count, today's count, and source distribution.

import logging
import time

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

# Recording the time the application started so we can calculate uptime.
_start_time = time.time()


@router.get("/live")
async def get_live_metrics() -> dict:
    # Returning live system metrics including the total article count from
    # PostgreSQL, the source distribution from MongoDB, and the application
    # uptime in seconds.
    try:
        from api.database.postgres import get_pool
        from api.database.mongo import count_by_source
        import psycopg2.extras

        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM articles;")
                total_articles = cur.fetchone()[0]

                # Counting articles collected today by comparing the collected_at
                # text field prefix with today's date string.
                from datetime import date
                today_str = date.today().isoformat()
                cur.execute(
                    "SELECT COUNT(*) FROM articles WHERE collected_at LIKE %s;",
                    (f"{today_str}%",),
                )
                today_articles = cur.fetchone()[0]
        finally:
            pool.putconn(conn)

        source_counts = count_by_source()
        uptime = round(time.time() - _start_time, 2)

        return {
            "status": "ok",
            "uptime_seconds": uptime,
            "total_articles": total_articles,
            "articles_today": today_articles,
            "source_distribution": source_counts,
        }
    except Exception as exc:
        logger.error("Fetching live metrics failing: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

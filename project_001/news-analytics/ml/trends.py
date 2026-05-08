# This file is detecting trending topics by counting keyword frequencies over a
# rolling time window. It is comparing the current window count against the previous
# window count to identify keywords that are growing in popularity. A keyword with
# a high trend score means it appeared much more in recent articles than before.

import logging
from collections import Counter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TrendDetector:

    def __init__(self, window_minutes: int = 60) -> None:
        # Setting up two counters: one for the current time window and one for
        # the previous window. Comparing them reveals which keywords are trending.
        self.window_minutes = window_minutes
        self._current: Counter = Counter()
        self._previous: Counter = Counter()
        self._window_start: datetime = datetime.utcnow()

    def _rotate_window(self) -> None:
        # Checking whether the current time window has expired and rotating the
        # counters if it has. The current counter becomes the previous counter
        # and a fresh counter starts for the new window.
        now = datetime.utcnow()
        if now - self._window_start >= timedelta(minutes=self.window_minutes):
            self._previous = self._current.copy()
            self._current = Counter()
            self._window_start = now
            logger.info("Trend detection window rotating")

    def ingest(self, keywords: list[str]) -> None:
        # Adding a list of keywords to the current window counter. Calling
        # rotate first so the counters stay aligned with real time.
        self._rotate_window()
        self._current.update(keywords)

    def get_trending(self, top_n: int = 20) -> list[dict]:
        # Computing the trending score for each keyword as the difference between
        # its current window count and its previous window count. Returning the
        # top N keywords sorted by trending score descending.
        self._rotate_window()
        trending: list[dict] = []
        all_keywords = set(self._current.keys()) | set(self._previous.keys())

        for keyword in all_keywords:
            current_count = self._current.get(keyword, 0)
            previous_count = self._previous.get(keyword, 0)
            trend_score = current_count - previous_count
            trending.append({
                "keyword": keyword,
                "current_count": current_count,
                "previous_count": previous_count,
                "trend_score": trend_score,
            })

        trending.sort(key=lambda x: x["trend_score"], reverse=True)
        return trending[:top_n]

# This file is handling Hacker News data collection. It is using the official
# Hacker News Firebase API to fetch the top story IDs and then downloading each
# story's details. Stories are fetched in parallel using threads so the collection
# finishes quickly even when downloading hundreds of items at once.

import logging
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)

# This is the base URL for the Hacker News Firebase REST API.
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsScraper:

    def __init__(self, max_stories: int = 100, max_workers: int = 10) -> None:
        # Storing how many stories to fetch and how many threads to use.
        # Using a session so connections are reused across all requests.
        self.max_stories = max_stories
        self.max_workers = max_workers
        self.session = requests.Session()

    def _get_top_story_ids(self) -> list[int]:
        # Fetching the list of top story IDs from Hacker News. Returning only
        # up to max_stories IDs so we do not download more than needed.
        url = f"{HN_API_BASE}/topstories.json"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        ids = response.json()
        return ids[: self.max_stories]

    def _get_story(self, story_id: int) -> dict | None:
        # Fetching a single story by its ID from the Hacker News item endpoint.
        # Returning None when the request fails so the caller can skip missing
        # items without the whole collection crashing.
        url = f"{HN_API_BASE}/item/{story_id}.json"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.warning("Fetching story %d failing: %s", story_id, exc)
            return None

    def fetch_top_stories(self) -> list[dict]:
        # Fetching all top stories in parallel and returning them as a list of
        # normalized dictionaries. Stories that returned None or are missing a
        # title are filtered out before returning.
        try:
            story_ids = self._get_top_story_ids()
            logger.info("Fetching %d Hacker News stories", len(story_ids))
        except requests.RequestException as exc:
            logger.error("Fetching Hacker News top story IDs failing: %s", exc)
            return []

        raw_stories: list[dict] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._get_story, sid): sid for sid in story_ids}
            for future in as_completed(futures):
                result = future.result()
                if result and result.get("title"):
                    raw_stories.append(result)

        logger.info("Collected %d valid Hacker News stories", len(raw_stories))
        return [self._normalize(s) for s in raw_stories]

    def _normalize(self, story: dict) -> dict:
        # Converting a raw Hacker News story into the standard format used across
        # the pipeline. Computing a unique ID from the story URL so deduplication
        # works the same way as for NewsAPI articles.
        url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}")
        article_id = hashlib.md5(url.encode()).hexdigest()
        published_ts = story.get("time", 0)
        published_at = datetime.utcfromtimestamp(published_ts).isoformat() if published_ts else ""
        return {
            "id": article_id,
            "title": story.get("title") or "",
            "description": story.get("text") or "",
            "content": story.get("text") or "",
            "url": url,
            "author": story.get("by") or "",
            "source_name": "Hacker News",
            "published_at": published_at,
            "collected_at": datetime.utcnow().isoformat(),
            "source": "hackernews",
            "category": "technology",
            "score": story.get("score", 0),
            "comments": story.get("descendants", 0),
        }

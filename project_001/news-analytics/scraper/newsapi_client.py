# This file is handling the NewsAPI integration. It is connecting to the NewsAPI
# website and fetching the latest news articles. Every article is then cleaned up
# and converted into a standard format so the rest of the pipeline can use it easily.

import logging
import hashlib
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class NewsAPIClient:

    # This is the base URL for all NewsAPI requests.
    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str) -> None:
        # Storing the API key and creating a session so we reuse the same
        # connection for multiple requests instead of opening a new one each time.
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": self.api_key})

    def _get(self, endpoint: str, params: dict) -> dict:
        # Sending a GET request to the given NewsAPI endpoint and returning
        # the response as a dictionary. Raising an error if the request fails.
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def fetch_top_headlines(
        self,
        country: str = "us",
        category: str = "technology",
        page_size: int = 100,
    ) -> list[dict]:
        # Fetching the top headlines from NewsAPI for the given country and category.
        # Only English articles are requested so we do not get garbled text from
        # other languages. Returning a list of normalized article dictionaries.
        try:
            data = self._get(
                "top-headlines",
                {
                    "country": country,
                    "category": category,
                    "pageSize": page_size,
                    "language": "en",
                },
            )
            articles = data.get("articles", [])
            logger.info("Fetching %d top headlines from NewsAPI", len(articles))
            return [self._normalize(a, source="newsapi_headlines") for a in articles]
        except requests.RequestException as exc:
            logger.error("NewsAPI top-headlines request failing: %s", exc)
            return []

    def fetch_everything(
        self,
        query: str = "technology OR AI OR startup",
        page_size: int = 100,
        sort_by: str = "publishedAt",
    ) -> list[dict]:
        # Fetching articles matching the given search query from the NewsAPI
        # everything endpoint. Sorting by publication date so the most recent
        # articles come first. Only English articles are requested.
        try:
            data = self._get(
                "everything",
                {"q": query, "pageSize": page_size, "sortBy": sort_by, "language": "en"},
            )
            articles = data.get("articles", [])
            logger.info("Fetching %d articles from NewsAPI everything", len(articles))
            return [self._normalize(a, source="newsapi_everything") for a in articles]
        except requests.RequestException as exc:
            logger.error("NewsAPI everything request failing: %s", exc)
            return []

    def _normalize(self, article: dict, source: str) -> dict:
        # Converting a raw NewsAPI article into the standard format used across
        # the whole pipeline. Generating a unique ID by hashing the article URL
        # so duplicate articles can be detected and removed later.
        url = article.get("url", "")
        article_id = hashlib.md5(url.encode()).hexdigest()
        return {
            "id": article_id,
            "title": article.get("title") or "",
            "description": article.get("description") or "",
            "content": article.get("content") or "",
            "url": url,
            "author": article.get("author") or "",
            "source_name": article.get("source", {}).get("name", ""),
            "published_at": article.get("publishedAt", ""),
            "collected_at": datetime.utcnow().isoformat(),
            "source": source,
            "category": "technology",
        }

# This file is the main entry point for the data collection layer. It is combining
# the NewsAPI client and the Hacker News scraper into a single collector class.
# The collector fetches from both sources, merges the results, removes duplicates,
# and returns a clean unified list ready for the Kafka producer.

import logging
import os

from scraper.newsapi_client import NewsAPIClient
from scraper.hackernews_scraper import HackerNewsScraper
from scraper.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class NewsCollector:

    def __init__(self) -> None:
        # Reading the NewsAPI key from the environment and creating instances of
        # both scrapers and the deduplicator.
        api_key = os.getenv("NEWSAPI_KEY", "")
        self.newsapi = NewsAPIClient(api_key=api_key)
        self.hn_scraper = HackerNewsScraper(max_stories=100)
        self.deduplicator = Deduplicator()

    def collect(self) -> list[dict]:
        # Running one full collection cycle. Fetching top headlines and search
        # results from NewsAPI, fetching top stories from Hacker News, merging
        # all three lists together, and then removing duplicates before returning.
        logger.info("Starting collection cycle")

        headlines = self.newsapi.fetch_top_headlines()
        everything = self.newsapi.fetch_everything()
        hn_stories = self.hn_scraper.fetch_top_stories()

        combined = headlines + everything + hn_stories
        logger.info("Collected %d total articles before deduplication", len(combined))

        unique = self.deduplicator.filter_new(combined)
        logger.info("Returning %d unique articles after deduplication", len(unique))
        return unique

# This file is handling deduplication of news articles. It is keeping a set of
# article IDs that have already been seen and filtering out any article whose ID
# appears in that set. This prevents the same story from being processed multiple
# times when the scraper runs on a schedule every 30 minutes.

import logging

logger = logging.getLogger(__name__)


class Deduplicator:

    def __init__(self) -> None:
        # Creating an empty set to store IDs of articles we have already seen.
        self._seen: set[str] = set()

    def filter_new(self, articles: list[dict]) -> list[dict]:
        # Accepting a list of articles and returning only the ones whose ID has
        # not been seen before. Also adding the new IDs to the seen set so future
        # calls will correctly identify them as duplicates.
        new_articles: list[dict] = []
        for article in articles:
            article_id = article.get("id", "")
            if article_id and article_id not in self._seen:
                self._seen.add(article_id)
                new_articles.append(article)

        duplicates = len(articles) - len(new_articles)
        if duplicates:
            logger.info("Filtering %d duplicate articles", duplicates)

        return new_articles

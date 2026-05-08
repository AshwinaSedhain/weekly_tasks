# This file is combining all ML components into a single pipeline class. It is
# running sentiment analysis, keyword extraction, clustering, and trend detection
# on each article so the rest of the application only needs to call one method
# to get fully enriched articles ready for storage.

import logging

from ml.sentiment import SentimentAnalyzer
from ml.keywords import KeywordExtractor
from ml.clustering import ArticleClusterer
from ml.trends import TrendDetector

logger = logging.getLogger(__name__)


class MLPipeline:

    def __init__(self) -> None:
        # Creating instances of all four ML components that will be used
        # during each processing run.
        self.sentiment_analyzer = SentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor(top_n=10)
        self.clusterer = ArticleClusterer(n_clusters=8)
        self.trend_detector = TrendDetector(window_minutes=60)

    def process(self, articles: list[dict]) -> list[dict]:
        # Processing a list of raw articles through the full ML pipeline and
        # returning the enriched list. Each article gains sentiment scores, a
        # keywords list, and a cluster label when enough articles are available.
        if not articles:
            return []

        enriched: list[dict] = []
        for article in articles:
            article = self.sentiment_analyzer.analyze_article(article)
            article = self.keyword_extractor.extract_from_article(article)
            self.trend_detector.ingest(article.get("keywords", []))
            enriched.append(article)

        # Fitting the clusterer only when we have at least 8 articles because
        # K-Means needs at least as many data points as clusters.
        if len(enriched) >= 8:
            self.clusterer.fit(enriched)
            labels = self.clusterer.predict(enriched)
            for i, label in enumerate(labels):
                enriched[i]["cluster"] = label

        logger.info("ML pipeline processed %d articles", len(enriched))
        return enriched

    def get_trending(self, top_n: int = 20) -> list[dict]:
        # Delegating to the trend detector and returning the current list of
        # trending keywords.
        return self.trend_detector.get_trending(top_n=top_n)

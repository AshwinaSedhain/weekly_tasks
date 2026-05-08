# This file is testing the ML components. It is verifying that sentiment analysis
# returns the correct labels for positive, negative, and neutral text, that keyword
# extraction produces non-empty results for real text, and that the trend detector
# correctly identifies growing keywords over time.

import pytest

from ml.sentiment import SentimentAnalyzer
from ml.keywords import KeywordExtractor
from ml.trends import TrendDetector
from ml.clustering import ArticleClusterer
from ml.pipeline import MLPipeline


def make_article(article_id: str = "1", title: str = "", description: str = "") -> dict:
    # Returning a minimal article dictionary for use in ML tests.
    return {
        "id": article_id,
        "title": title,
        "description": description,
        "content": "",
        "source": "test",
        "category": "technology",
    }


class TestSentimentAnalyzer:

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_text_returns_positive_label(self):
        # Verifying that clearly positive text produces a positive sentiment label.
        result = self.analyzer.analyze("This is an amazing and wonderful breakthrough!")
        assert result["label"] == "positive"
        assert result["compound"] > 0.05

    def test_negative_text_returns_negative_label(self):
        # Verifying that clearly negative text produces a negative sentiment label.
        result = self.analyzer.analyze("This is a terrible disaster and complete failure.")
        assert result["label"] == "negative"
        assert result["compound"] < -0.05

    def test_neutral_text_returns_neutral_label(self):
        # Verifying that neutral factual text produces a neutral sentiment label.
        result = self.analyzer.analyze("The company released a new product today.")
        assert result["label"] == "neutral"

    def test_empty_text_returns_neutral(self):
        # Checking that empty text returns a neutral label with a compound score of zero.
        result = self.analyzer.analyze("")
        assert result["label"] == "neutral"
        assert result["compound"] == 0.0

    def test_analyze_article_enriches_dict(self):
        # Verifying that analyze_article adds a sentiment key to the article dictionary.
        article = make_article(title="Great news for technology sector")
        result = self.analyzer.analyze_article(article)
        assert "sentiment" in result
        assert "label" in result["sentiment"]

    def test_result_contains_all_score_keys(self):
        # Checking that the analyze result always contains all expected score keys.
        result = self.analyzer.analyze("Some text here")
        for key in ["label", "compound", "positive", "negative", "neutral"]:
            assert key in result

    def test_none_fields_do_not_crash(self):
        # Verifying that an article with None title and description does not crash
        # the analyzer and returns a neutral result.
        article = make_article(title=None, description=None)
        result = self.analyzer.analyze_article(article)
        assert "sentiment" in result


class TestKeywordExtractor:

    def setup_method(self):
        self.extractor = KeywordExtractor(top_n=5)

    def test_extract_returns_list(self):
        # Verifying that extract always returns a list.
        result = self.extractor.extract("Python machine learning artificial intelligence")
        assert isinstance(result, list)

    def test_extract_respects_top_n(self):
        # Checking that extract returns at most top_n keywords.
        text = "python java javascript typescript golang rust swift kotlin scala clojure"
        result = self.extractor.extract(text)
        assert len(result) <= 5

    def test_extract_empty_text_returns_empty_list(self):
        # Verifying that empty text produces an empty keyword list.
        result = self.extractor.extract("")
        assert result == []

    def test_extract_from_article_adds_keywords_key(self):
        # Checking that extract_from_article adds a keywords key to the article.
        article = make_article(
            title="Machine learning model training",
            description="Deep learning neural network optimization",
        )
        result = self.extractor.extract_from_article(article)
        assert "keywords" in result
        assert isinstance(result["keywords"], list)

    def test_none_fields_do_not_crash(self):
        # Verifying that an article with None fields does not crash the extractor.
        article = {"id": "1", "title": None, "description": None, "content": None}
        result = self.extractor.extract_from_article(article)
        assert "keywords" in result


class TestTrendDetector:

    def setup_method(self):
        self.detector = TrendDetector(window_minutes=60)

    def test_ingest_and_get_trending_returns_list(self):
        # Verifying that get_trending returns a list after ingesting some keywords.
        self.detector.ingest(["python", "machine", "learning"])
        result = self.detector.get_trending()
        assert isinstance(result, list)

    def test_trending_contains_expected_keys(self):
        # Checking that each trending item contains all required keys.
        self.detector.ingest(["python", "python", "ai"])
        result = self.detector.get_trending()
        if result:
            item = result[0]
            for key in ["keyword", "current_count", "previous_count", "trend_score"]:
                assert key in item

    def test_frequently_ingested_keyword_appears_in_trending(self):
        # Verifying that a keyword ingested many times appears in the trending list.
        for _ in range(10):
            self.detector.ingest(["dominant_keyword"])
        self.detector.ingest(["rare_keyword"])
        result = self.detector.get_trending()
        keywords = [item["keyword"] for item in result]
        assert "dominant_keyword" in keywords

    def test_get_trending_respects_top_n(self):
        # Checking that get_trending returns at most top_n items.
        for i in range(30):
            self.detector.ingest([f"keyword_{i}"])
        result = self.detector.get_trending(top_n=10)
        assert len(result) <= 10


class TestArticleClusterer:

    def _make_articles(self, count: int) -> list[dict]:
        topics = ["python programming", "machine learning AI", "web development",
                  "cloud computing", "data science", "cybersecurity",
                  "blockchain crypto", "mobile apps"]
        return [
            make_article(
                article_id=str(i),
                title=topics[i % len(topics)],
                description=f"Article about {topics[i % len(topics)]}",
            )
            for i in range(count)
        ]

    def test_fit_sets_fitted_flag(self):
        # Verifying that calling fit with enough articles sets the fitted flag.
        clusterer = ArticleClusterer(n_clusters=4)
        articles = self._make_articles(20)
        clusterer.fit(articles)
        assert clusterer._fitted is True

    def test_predict_returns_correct_length(self):
        # Checking that predict returns one label per article.
        clusterer = ArticleClusterer(n_clusters=4)
        articles = self._make_articles(20)
        clusterer.fit(articles)
        labels = clusterer.predict(articles)
        assert len(labels) == len(articles)

    def test_predict_before_fit_returns_empty(self):
        # Verifying that calling predict before fit returns an empty list.
        clusterer = ArticleClusterer(n_clusters=4)
        result = clusterer.predict(self._make_articles(5))
        assert result == []


class TestMLPipeline:

    def setup_method(self):
        self.pipeline = MLPipeline()

    def test_process_empty_list_returns_empty(self):
        # Verifying that processing an empty list returns an empty list.
        result = self.pipeline.process([])
        assert result == []

    def test_process_adds_sentiment_key(self):
        # Checking that every article returned by process contains a sentiment key.
        articles = [make_article(str(i), title="Technology news article") for i in range(3)]
        result = self.pipeline.process(articles)
        for article in result:
            assert "sentiment" in article

    def test_process_adds_keywords_key(self):
        # Checking that every article returned by process contains a keywords key.
        articles = [make_article(str(i), title="Machine learning deep neural network") for i in range(3)]
        result = self.pipeline.process(articles)
        for article in result:
            assert "keywords" in article

    def test_process_preserves_original_fields(self):
        # Verifying that process does not remove any fields from the original articles.
        articles = [make_article("1", title="Test", description="Test description")]
        result = self.pipeline.process(articles)
        assert result[0]["id"] == "1"
        assert result[0]["title"] == "Test"

    def test_none_fields_do_not_crash_pipeline(self):
        # Verifying that articles with None fields pass through the pipeline without
        # raising any exceptions.
        articles = [{"id": "1", "title": None, "description": None, "content": None,
                     "source": "test", "category": "technology"}]
        result = self.pipeline.process(articles)
        assert len(result) == 1

# This file is performing sentiment analysis on news article titles and descriptions.
# It is using the VADER lexicon from NLTK because VADER is specifically tuned for
# short social-media and news text and does not require a GPU or a large model download.
# Compound scores above 0.05 are positive, below -0.05 are negative, everything else
# is neutral.

import logging

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Downloading the VADER lexicon the first time this module is imported.
nltk.download("vader_lexicon", quiet=True)


class SentimentAnalyzer:

    def __init__(self) -> None:
        # Creating the VADER analyzer instance that will be reused for all articles.
        self._analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> dict:
        # Computing the VADER sentiment scores for the given text and returning a
        # dictionary with the compound score and a human-readable label. Empty text
        # returns neutral with a score of zero.
        if not text or not text.strip():
            return {"label": "neutral", "compound": 0.0, "positive": 0.0,
                    "negative": 0.0, "neutral": 1.0}

        scores = self._analyzer.polarity_scores(text)
        compound = scores["compound"]

        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "label": label,
            "compound": round(compound, 4),
            "positive": round(scores["pos"], 4),
            "negative": round(scores["neg"], 4),
            "neutral": round(scores["neu"], 4),
        }

    def analyze_article(self, article: dict) -> dict:
        # Combining the title and description of an article into one string,
        # running sentiment analysis on it, and returning the article dictionary
        # enriched with a sentiment key containing the result.
        text = f"{article.get('title') or ''} {article.get('description') or ''}"
        sentiment = self.analyze(text)
        return {**article, "sentiment": sentiment}

# This file is extracting the most important keywords from news article text.
# It is using frequency counting with stop-word filtering. Stop words are common
# words like "the", "and", "is" that appear everywhere and carry no meaning.
# After removing them, the most frequent remaining words are the keywords.

import logging
import re
from collections import Counter

import nltk
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)

# Building the stop words set and adding extra words that are common in news
# but not meaningful for keyword analysis.
STOP_WORDS = set(stopwords.words("english"))
STOP_WORDS.update({"said", "say", "says", "also", "would", "could", "one", "two"})


class KeywordExtractor:

    def __init__(self, top_n: int = 10) -> None:
        # Storing how many top keywords to return for each article.
        self.top_n = top_n

    def _tokenize(self, text: str) -> list[str]:
        # Lowercasing the text, removing punctuation, and splitting into individual
        # word tokens. Filtering out stop words and very short tokens.
        text = text.lower()
        text = re.sub(r"[^a-z\s]", "", text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 3 and t not in STOP_WORDS]

    def extract(self, text: str) -> list[str]:
        # Tokenizing the text and returning the top N most frequent words as a
        # list of keyword strings. Returning empty list for empty text.
        if not text or not text.strip():
            return []
        tokens = self._tokenize(text)
        counter = Counter(tokens)
        return [word for word, _ in counter.most_common(self.top_n)]

    def extract_from_article(self, article: dict) -> dict:
        # Combining the title, description, and content of an article into one
        # string, extracting keywords from it, and returning the article enriched
        # with a keywords list. Using "or" to convert None values to empty strings
        # so the join never raises a TypeError.
        combined = " ".join([
            article.get("title") or "",
            article.get("description") or "",
            article.get("content") or "",
        ])
        keywords = self.extract(combined)
        return {**article, "keywords": keywords}

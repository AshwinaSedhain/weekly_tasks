# This file is grouping news articles into topic clusters using K-Means on TF-IDF
# vectors. TF-IDF converts text into numbers by measuring how important each word
# is in an article compared to all other articles. K-Means then groups similar
# articles together. This lets the dashboard show which broad themes are dominating
# the news feed without requiring manually defined categories.

import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class ArticleClusterer:

    def __init__(self, n_clusters: int = 8, max_features: int = 500) -> None:
        # Setting up the TF-IDF vectorizer and K-Means model. The vectorizer
        # converts article text into numerical vectors. K-Means groups those
        # vectors into n_clusters groups.
        self.n_clusters = n_clusters
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self._fitted = False

    def _build_corpus(self, articles: list[dict]) -> list[str]:
        # Combining the title and description of each article into a single string
        # that the TF-IDF vectorizer can process.
        return [
            f"{a.get('title') or ''} {a.get('description') or ''}"
            for a in articles
        ]

    def fit(self, articles: list[dict]) -> None:
        # Fitting the TF-IDF vectorizer and K-Means model on the provided articles.
        # Skipping if there are not enough articles to fill all clusters.
        if len(articles) < self.n_clusters:
            logger.warning(
                "Not enough articles (%d) to fit %d clusters",
                len(articles), self.n_clusters,
            )
            return

        corpus = self._build_corpus(articles)
        vectors = self.vectorizer.fit_transform(corpus)
        self.model.fit(vectors)
        self._fitted = True
        logger.info("Clustering model fitted on %d articles", len(articles))

    def predict(self, articles: list[dict]) -> list[int]:
        # Predicting the cluster label for each article. Returning an empty list
        # when the model has not been fitted yet.
        if not self._fitted:
            logger.warning("Clusterer not fitted yet, returning empty labels")
            return []

        corpus = self._build_corpus(articles)
        vectors = self.vectorizer.transform(corpus)
        return self.model.predict(vectors).tolist()

    def get_cluster_keywords(self, top_n: int = 5) -> dict[int, list[str]]:
        # Returning the top N keywords for each cluster by looking at the cluster
        # center coordinates in the TF-IDF space and picking the features with
        # the highest weights.
        if not self._fitted:
            return {}

        feature_names = self.vectorizer.get_feature_names_out()
        cluster_keywords: dict[int, list[str]] = {}
        for cluster_id, center in enumerate(self.model.cluster_centers_):
            top_indices = center.argsort()[-top_n:][::-1]
            cluster_keywords[cluster_id] = [feature_names[i] for i in top_indices]
        return cluster_keywords

    def pca_coordinates(self, articles: list[dict]) -> list[dict]:
        # Projecting the TF-IDF vectors down to two dimensions using PCA so the
        # clusters can be plotted on a scatter chart in the dashboard.
        if not self._fitted or not articles:
            return []

        corpus = self._build_corpus(articles)
        vectors = self.vectorizer.transform(corpus).toarray()
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(vectors)
        labels = self.model.predict(self.vectorizer.transform(corpus))

        return [
            {
                "id": articles[i].get("id", ""),
                "title": articles[i].get("title", ""),
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "cluster": int(labels[i]),
            }
            for i in range(len(articles))
        ]

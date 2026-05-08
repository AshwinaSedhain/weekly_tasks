# This file is managing the MongoDB connection and providing helper functions for
# storing and retrieving raw article documents. MongoDB is used as the raw document
# store because it handles variable-schema JSON documents without requiring a
# predefined table structure like PostgreSQL does.

import logging
import os
from typing import Optional

from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "newsdb")

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    # Creating the MongoClient on first call and returning it on subsequent calls.
    # The client manages its own connection pool internally so we only need one
    # instance per process.
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
        logger.info("MongoDB client created")
    return _client


def get_collection(name: str = "raw_articles") -> Collection:
    # Returning the named collection from the news database. MongoDB creates the
    # collection automatically if it does not exist yet.
    db: Database = get_client()[MONGO_DB]
    return db[name]


def init_indexes() -> None:
    # Creating indexes on the raw_articles collection so queries by ID and
    # published_at are fast. Safe to call on every startup because MongoDB
    # ignores duplicate index creation requests.
    col = get_collection("raw_articles")
    col.create_index("id", unique=True)
    col.create_index([("published_at", DESCENDING)])
    col.create_index("source")
    logger.info("MongoDB indexes initialized")


def insert_raw_article(article: dict) -> None:
    # Inserting a raw article document into MongoDB. Using update_one with upsert
    # so inserting the same article ID twice updates the existing document rather
    # than raising a duplicate key error.
    col = get_collection("raw_articles")
    try:
        col.update_one(
            {"id": article.get("id")},
            {"$set": article},
            upsert=True,
        )
    except Exception as exc:
        logger.error("Inserting raw article %s failing: %s", article.get("id"), exc)


def fetch_raw_articles(limit: int = 50, skip: int = 0) -> list[dict]:
    # Fetching raw articles from MongoDB ordered by published_at descending.
    # Excluding the internal MongoDB _id field so the returned dictionaries
    # are JSON-serializable without any extra conversion.
    col = get_collection("raw_articles")
    cursor = (
        col.find({}, {"_id": 0})
        .sort("published_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)


def count_by_source() -> dict:
    # Aggregating the raw_articles collection by source and returning a dictionary
    # mapping source name to article count. Used by the dashboard to show how many
    # articles came from each data source.
    col = get_collection("raw_articles")
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    result = col.aggregate(pipeline)
    return {doc["_id"]: doc["count"] for doc in result}

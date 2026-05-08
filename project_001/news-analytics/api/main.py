# This file is the entry point for the FastAPI application. It is creating the app
# instance, registering all routers, setting up logging, and initializing the database
# connections when the application starts up for the first time.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import news, analytics, scrape, metrics
from api.database.postgres import init_schema
from api.database.mongo import init_indexes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Running startup logic when the application begins. Initializing the PostgreSQL
    # schema and MongoDB indexes so the application is ready to serve requests
    # immediately without any manual setup.
    logger.info("Application starting up")
    try:
        init_schema()
        init_indexes()
    except Exception as exc:
        logger.error("Database initialization failing: %s", exc)
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="News Analytics API",
    description="Real-time news analytics and intelligent data pipeline API",
    version="1.0.0",
    lifespan=lifespan,
)

# Allowing all origins so the dashboard running on port 8050 can call the API
# running on port 8000 without being blocked by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router, prefix="/news", tags=["News"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(scrape.router, prefix="/scrape", tags=["Scrape"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])


@app.get("/health")
async def health_check() -> dict:
    # Returning a simple health check response so load balancers and Kubernetes
    # liveness probes can verify the service is running.
    return {"status": "ok", "service": "news-analytics-api"}

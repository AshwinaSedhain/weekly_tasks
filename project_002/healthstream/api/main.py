# Entry point for the FastAPI application. Register routers and middleware here.
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from config import settings
from database import engine
from routers import claims, analytics, fraud, patients, hospitals
from schemas import HealthCheck

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def wait_for_db(retries: int = 20, delay: int = 3):
    # Block startup until the database is reachable.
    for attempt in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except OperationalError:
            logger.warning("Waiting for database (attempt %d/%d)", attempt + 1, retries)
            time.sleep(delay)
    logger.error("Could not connect to database after %d attempts", retries)


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    logger.info("Healthstream API starting up")
    yield
    logger.info("Healthstream API shutting down")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "Healthcare data engineering platform API. "
        "Provides claims data, fraud detection, analytics, and patient/hospital insights."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims.router)
app.include_router(analytics.router)
app.include_router(fraud.router)
app.include_router(patients.router)
app.include_router(hospitals.router)


@app.get("/health", response_model=HealthCheck, tags=["System"])
def health_check():
    # Ping the database to confirm connectivity.
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        db_status = "unhealthy"

    return HealthCheck(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        version=settings.api_version,
    )


@app.get("/", tags=["System"])
def root():
    return {
        "service": "Healthstream API",
        "version": settings.api_version,
        "docs":    "/docs",
    }

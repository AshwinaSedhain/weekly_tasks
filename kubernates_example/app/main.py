import os
from fastapi import FastAPI

# Creates the FastAPI app instance with a title
app = FastAPI(title="K8s Demo App")

# Reads the app version from environment variable, defaults to "v1" if not set
APP_VERSION = os.getenv("APP_VERSION", "v1")

# Reads the message from environment variable, defaults to a hardcoded string if not set
APP_MESSAGE = os.getenv("APP_MESSAGE", "Hello from Kubernetes v1")


@app.get("/")
def root():
    # Returns the message and version injected from the ConfigMap
    return {
        "message": APP_MESSAGE,
        "version": APP_VERSION,
    }


@app.get("/version")
def version():
    # Returns only the app version
    return {"version": APP_VERSION}


@app.get("/health")
def health():
    # Kubernetes uses this endpoint to check if the container is alive (liveness probe)
    return {"status": "ok"}


@app.get("/ready")
def ready():
    # Kubernetes uses this endpoint to check if the container is ready to receive traffic (readiness probe)
    return {"status": "ready"}

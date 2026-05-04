# Starting the Smart Task Manager API
# Entry point for the FastAPI application.
# Running with: uvicorn main:app --reload

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from database import Base, engine
from routes.tasks import router as tasks_router

# Creating all database tables on startup
Base.metadata.create_all(bind=engine)

# Initializing the FastAPI application with metadata
app = FastAPI(
    title="Smart Task Manager API",
    description=(
        "A RESTful API for managing tasks with CRUD operations, "
        "filtering, pagination, and token-based authentication.\n\n"
        "**Authentication:** All `/tasks` endpoints require an "
        "`Authorization: Bearer <token>` header.  "
        "The default development token is `777777`."
    ),
    version="1.0.0",
    contact={
        "name": "Smart Task Manager",
        "url": "https://github.com/example/smart-task-manager",
    },
    license_info={
        "name": "MIT",
    },
)

# Handling Pydantic validation errors and returning a clean 400 response
@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    try:
        errors = exc.errors()
    except Exception:
        errors = str(exc)
    return JSONResponse(
        status_code=400,
        content={"detail": errors},
    )


# Catching all unexpected server errors and returning a 500 response
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Registering the tasks router
app.include_router(tasks_router)


# Returning 200 OK when the service is running
@app.get("/health", tags=["Health"], summary="Health check")
def health_check():
    return {"status": "ok"}

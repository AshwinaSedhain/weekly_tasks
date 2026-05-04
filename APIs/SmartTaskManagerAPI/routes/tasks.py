# Handling task CRUD routes with filtering, pagination, and token-based auth.

import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from auth import verify_token
from database import get_db
from models import (
    ErrorResponse,
    PaginatedTaskResponse,
    PriorityEnum,
    StatusEnum,
    TaskCreate,
    TaskModel,
    TaskResponse,
    TaskUpdate,
)

# Registering all routes under /tasks, requiring a valid Bearer token for every request
router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(verify_token)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)


# Fetching a task by ID and raising HTTP 404 if not found
def _get_task_or_404(task_id: int, db: Session) -> TaskModel:
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Task with id={task_id} not found",
        )
    return task


# Creating a new task with a required title and optional fields
@router.post(
    "/",
    response_model=TaskResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskModel:
    task = TaskModel(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Listing all tasks and applying optional filters for status and priority
# Supporting pagination through page and limit query parameters
@router.get(
    "/",
    response_model=PaginatedTaskResponse,
    status_code=http_status.HTTP_200_OK,
    summary="List tasks with optional filtering and pagination",
)
def list_tasks(
    status_filter: Optional[StatusEnum] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[PriorityEnum] = Query(None, alias="priority", description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
) -> PaginatedTaskResponse:
    query = db.query(TaskModel)

    # Applying filters only when values are provided
    if status_filter is not None:
        query = query.filter(TaskModel.status == status_filter)
    if priority_filter is not None:
        query = query.filter(TaskModel.priority == priority_filter)

    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 1

    # Ordering by newest first and slicing the results for the requested page
    items = (
        query
        .order_by(TaskModel.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return PaginatedTaskResponse(
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        items=[TaskResponse.from_orm(item) for item in items],
    )


# Retrieving a single task by its ID
@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get a single task by ID",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> TaskModel:
    return _get_task_or_404(task_id, db)


# Updating one or more fields of an existing task
# Modifying only the fields that are included in the request body
@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Update a task",
)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskModel:
    task = _get_task_or_404(task_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    # Applying each changed field onto the task object
    for field, value in update_data.items():
        setattr(task, field, value)

    # Updating the timestamp manually since SQLite does not support onupdate triggers
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task


# Deleting a task permanently by its ID
@router.delete(
    "/{task_id}",
    status_code=http_status.HTTP_200_OK,
    summary="Delete a task",
    responses={200: {"description": "Task deleted successfully"}},
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> dict:
    task = _get_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
    return {"detail": f"Task with id={task_id} deleted successfully"}

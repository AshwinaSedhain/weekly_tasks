# Defining SQLAlchemy ORM models and Pydantic schemas for the Task Manager API.
# Compatible with Pydantic v2.

from datetime import datetime, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy import Column, Integer, String, DateTime, Date, Enum as SAEnum
from sqlalchemy.sql import func

from database import Base


# Defining allowed values for task status
class StatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"


# Defining allowed values for task priority
class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# Representing the "tasks" table in the SQLite database
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    status = Column(SAEnum(StatusEnum), default=StatusEnum.pending, nullable=False)
    priority = Column(SAEnum(PriorityEnum), default=PriorityEnum.medium, nullable=False)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Sharing common fields across create and response schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Buy groceries"])
    description: Optional[str] = Field(None, max_length=1000, examples=["Milk, eggs, bread"])
    status: StatusEnum = Field(StatusEnum.pending, examples=["pending"])
    priority: PriorityEnum = Field(PriorityEnum.medium, examples=["medium"])
    due_date: Optional[date] = Field(None, examples=["2026-06-01"])

    # Ensuring the title is not just whitespace
    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


# Accepting task data when creating a new task via POST /tasks/
class TaskCreate(TaskBase):
    pass


# Accepting partial task data when updating via PUT /tasks/{id}
# All fields are optional — only provided fields will be updated
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, examples=["Buy groceries"])
    description: Optional[str] = Field(None, max_length=1000, examples=["Milk, eggs, bread"])
    status: Optional[StatusEnum] = Field(None, examples=["completed"])
    priority: Optional[PriorityEnum] = Field(None, examples=["high"])
    due_date: Optional[date] = Field(None, examples=["2026-06-01"])

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v.strip() if v else v


# Returning task data in API responses including id and timestamps
# Setting from_attributes=True to allow converting SQLAlchemy ORM objects to Pydantic models
class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Wrapping paginated list responses with metadata
class PaginatedTaskResponse(BaseModel):
    total: int = Field(..., description="Total number of matching tasks")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    items: list[TaskResponse]


# Representing standard error responses for 4xx and 5xx status codes
class ErrorResponse(BaseModel):
    detail: str

from pydantic import BaseModel


# defining the shape of incoming todo data
class TodoCreate(BaseModel):
    title: str


# defining the shape of outgoing todo data
class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool

    class Config:
        from_attributes = True

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database

# creating the FastAPI app instance
app = FastAPI(title="Todo API")

# creating all database tables on startup
models.Base.metadata.create_all(bind=database.engine)


# providing a database session for each request
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# handling POST /todos — creating a new todo
@app.post("/todos", response_model=schemas.TodoResponse, status_code=201)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    new_todo = models.Todo(title=todo.title, completed=False)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo


# handling GET /todos — returning all todos
@app.get("/todos", response_model=List[schemas.TodoResponse])
def list_todos(db: Session = Depends(get_db)):
    return db.query(models.Todo).all()


# handling DELETE /todos/{id} — removing a todo by id
@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()

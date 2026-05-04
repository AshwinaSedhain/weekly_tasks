from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Define what a user should look like (data validation)
class User(BaseModel):
    id: int
    name: str

class UserCreate(BaseModel):
    name: str

# Fake database
users = [
    {"id": 1, "name": "potatoes"},
    {"id": 2, "name": "tomatoesS"}
]

# GET all users
@app.get('/users', response_model=List[User])
def get_users():
    return users

# POST a new user
@app.post('/users', response_model=User, status_code=201)
def create_user(user: UserCreate):
    new_user = User(id=len(users)+1, name=user.name)
    users.append(new_user.dict())
    return new_user


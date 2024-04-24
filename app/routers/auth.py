from starlette import status

from app.database import SessionLocal
from app.models import Users
from typing import Annotated
from fastapi import APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from passlib.context import CryptContext


router = APIRouter()

bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str

#Function for opening and closing connection with the database after each query.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependancy = Annotated[Session, Depends(get_db)]
@router.post("/auth",status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependancy,create_user_request: CreateUserRequest):

    create_user_model = Users(
        username=create_user_request.username,
        email=create_user_request.email,
        role=create_user_request.role,
        created_at= datetime.now(),
        updated_at= datetime.now(),
        password= bcrypt_context.hash(create_user_request.password)
    )
    db.add(create_user_model)
    db.commit()

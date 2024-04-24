from starlette import status

from app.database import SessionLocal
from app.models import Users
from typing import Annotated
from fastapi import APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.


router = APIRouter()
# Determine the current running environment

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = 'HS256'


bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

#Function for opening and closing connection with the database after each query.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependancy = Annotated[Session, Depends(get_db)]
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username== username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(username:str, user_id: int , expires_delta: timedelta):
    encode = {'sub':username , 'id':user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

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

@router.post("/token",response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependancy):

    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        return 'Failed Authentication'
    token = create_access_token(user.username, user.id, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}
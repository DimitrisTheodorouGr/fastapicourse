from starlette import status

from app.database import SessionLocal
from app.models import Users
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)
# Determine the current running environment

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = 'HS256'


bcrypt_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/login')

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=6)

class UpdateUserRequest(BaseModel):
    username: str
    email: str
class Token(BaseModel):
    access_token: str
    token_type: str
class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)
#Function for opening and closing connection with the database after each query.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username== username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(username:str, user_id: int ,user_role: str, expires_delta: timedelta):
    encode = {'sub':username , 'id':user_id , 'role':user_role}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def  get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not validate user")
        return {'username': username, 'user_id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not validate user")
#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.put("/update-info", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_info(user: user_dependency, db: db_dependency, update_user_request: UpdateUserRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    user_model2 = db.query(Users).filter(Users.id == user.get('user_id')).first()
    if user_model2 is None:
        raise HTTPException(status_code=404, detail='User not found.')

    user_model2.username = update_user_request.username
    user_model2.email = update_user_request.email
    user_model2.updated_at = datetime.now()

    db.add(user_model2)
    db.commit()
@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,create_user_request: CreateUserRequest):

    create_user_model = Users(
        username=create_user_request.username,
        email=create_user_request.email,
        role='user',
        created_at= datetime.now(),
        updated_at= datetime.now(),
        password= bcrypt_context.hash(create_user_request.password)
        )
    db.add(create_user_model)
    db.commit()

@router.put("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency,
                          user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    user_model = db.query(Users).filter(Users.id == user.get('user_id')).first()

    if not bcrypt_context.verify(user_verification.password, user_model.password):
        raise HTTPException(status_code=401, detail='Error on password change')
    user_model.password = bcrypt_context.hash(user_verification.new_password)
    user_model.updated_at = datetime.now()
    db.add(user_model)
    db.commit()
@router.post("/login",response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):

    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}


from app.database import SessionLocal
from app.models import Users, Ranches , UserRanches
from .auth import get_current_user
from fastapi import FastAPI, Depends, APIRouter,HTTPException
from typing import Union, Annotated
from sqlalchemy import text
from starlette import status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import os


router = APIRouter(
    prefix='/ranch',
    tags=['Ranch']
)

class CreateRanchRequest(BaseModel):
    name: str


#Function for opening and closing connection with the database after each query.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Example API endpoint
@router.get("/")
async def read_all_ranches_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher':
        return db.query(Ranches).join(UserRanches, UserRanches.ranch_id == Ranches.id).filter(UserRanches.user_id == user.get('user_id')).first()
    elif user.get('user_role') == 'admin':
        return db.query(Ranches).all()


@router.post('/')
async def create_ranch(user: user_dependency, db: db_dependency, create_ranch_request: CreateRanchRequest):

    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    create_ranch_model = Ranches(
        name=create_ranch_request.name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(create_ranch_model)
    db.commit()
@router.put("/{ranch_id}")
async def update_ranch(user: user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

@router.delete("/{ranch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ranch(user:user_dependency,db: db_dependency, ranch_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    ranch_model = db.query(Ranches).filter(Ranches.id == ranch_id).first()
    if ranch_model is None:
        raise HTTPException(status_code=404, detail='User not found.')

    db.query(Ranches).filter(Ranches.id == ranch_id).delete()
    db.commit()
